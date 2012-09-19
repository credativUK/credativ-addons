# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2009 credativ Ltd (<http://credativ.co.uk>).
#    All Rights Reserved
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import logging
import re
import time

from osv import osv, fields
from openerp.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT
from tools.translate import _
import itertools
import netsvc

import util


class order_edit(object):

    def _consolidate_edit_lines(self, cr, uid, original_ids, order, context):
        """
        Given an original order, and an edit order:
         * Check that no done lines are reduced.
         * Remove all lines from the edit order.
         * Recreate up to two lines for each product:
           - one for shipped items, and
           - one for unshipped items
         * Return a list of done lines.
        """
        original = self.browse(cr, uid, original_ids[0], context)

        done_totals = {}
        moves = []
        for picking in original.picking_ids:
            for move in picking.move_lines:
                moves.append(move)
                if move.state in ['done','assigned']:
                    done_totals[move.product_id] = done_totals.setdefault(move.product_id, 0) + move.product_qty

        # Get a list of lines for each product in the edit sale order
        edit_totals = {}
        for line in order.order_line:
            if line.product_id.id == False or line.product_id.type == 'service':
                continue
            if self._name == 'sale.order':
                qty = line.product_uom_qty
            else:
                qty = line.product_qty
            edit_totals[line.product_id] = edit_totals.setdefault(line.product_id, 0) + qty

        # Check that the totals in the edit aren't less than the shipped qty
        for product, done_total in done_totals.iteritems():
            if edit_totals.get(product, 0) < done_total:
                raise osv.except_osv(_('Error !'),
                                     _('There must be at least %d of %s in'
                                       ' the edited sale order, as they have'
                                       ' already been assigned or shipped.'
                                            % (done_total, product.name)))

        new_vals = {}
        for line in order.order_line:
            if line.product_id.id == False or line.product_id.type == 'service':
                continue
            new_vals[line.product_id.id] = {'price_unit': line.price_unit}
            if self._name == 'purchase.order':
                new_vals[line.product_id.id].update({'date_planned': line.date_planned})
            if self._name == 'sale.order':
                line.button_cancel()
            line.unlink()

        def add_product_order_line(product_id, qty):
            line_obj = self.pool.get(order.order_line[0]._name)
            product = self.pool.get('product.product').browse(cr, uid, product_id)

            #type: make_to_stock is default in sale.order.line
            vals = {'order_id': order.id,
                    'name': product.name,
                    'product_id': product.id,
                    'product_uom': product.uom_id.id,
                    }

            if self._name == 'sale.order':
                vals.update({'product_uom_qty': qty})

            vals.update(new_vals[product.id])

            line_id = line_obj.create(cr, uid, vals)
            if self._name == 'sale.order':
                line_obj.browse(cr, uid, line_id).button_confirm()
            return line_id

        line_moves = {}
        for m in moves:
            if m.state in ['done', 'assigned']:
                line_id = add_product_order_line(m.product_id.id, m.product_qty)
                line_moves[line_id] = m

        for product, edit_total in edit_totals.iteritems():
            remainder = edit_total - done_totals.get(product, 0)
            if remainder > 0:
                add_product_order_line(product.id, remainder)

        return line_moves

    def check_consolidation(self, cr, uid, ids, context=None):
        # TODO: edit with available moves
        # move may be made available after the initial copy so can't give a warning then
        # need to change confirm button to run an action that warns user of the available move
        # and then trigger the workflow to continue the current behaviour
        line_moves = None
        for order in self.browse(cr, uid, ids, context):
            original_ids = None
            if order.origin:
                original_ids = self.search(cr, uid, [('name', '=', order.origin)], context)
            if original_ids:
                line_moves = self._consolidate_edit_lines(cr, uid, original_ids,
                                                          order, context)
        return line_moves

    def copy_for_edit(self, cr, uid, id, context=None):
        if context is None:
            context = {}
        context = context.copy()
        context['order_edit'] = True
        try:
            if len(id) == 1:
                id = id[0]
        except TypeError:
            pass
        order = self.browse(cr, uid, id, context)

        order_states = {
            'sale.order':     ('progress','manual'),
            'purchase.order': ('confirmed','approved'),
            }

        if order.state in order_states[self._name]:
            new_id = self.copy(cr, uid, id, context=context)
            original_order_name = re.sub('-edit[0-9]+$', '', order.name)
            similar_name_ids = self.search(cr, uid, [('name', 'like', original_order_name + '%')])
            similar_names = set(similar_order['name'] for similar_order in self.read(cr, uid, similar_name_ids, ['name']))
            for i in itertools.count(1):
                new_name = '%s-edit%d' % (original_order_name, i)
                if new_name not in similar_names:
                    break
            vals = {'name': new_name, 'origin': order.name}

            self.write(cr, uid, new_id, vals)

            if self._name == 'purchase.order':
                wf_service = netsvc.LocalService('workflow')
                wf_service.trg_validate(uid, self._name, new_id, 'purchase_confirm', cr)

            return new_id
        else:
            raise osv.except_osv('Could not copy order', 'Order should be in progress.')

class sale_order(osv.osv, order_edit):
    _inherit = 'sale.order'

    def _refund_check_order(self, sale, cancel_assigned, accept_done):
        if sale.state not in ('progress', 'manual'):
            raise osv.except_osv(_('Error !'), _('Sale order is not in progress.'))

        # Check picking states
        for pick in sale.picking_ids:
            if not cancel_assigned and pick.state == 'assigned':
                raise self.RefundStockAssignedException(_('Error !'),
                    _('Stock has already been assigned - please cancel pickings manually'))
            if not accept_done and pick.state == 'done':
                raise osv.except_osv(_('Error !'),
                    _('Stock has already been shipped - please process manually'))

    def _check_invoices(self, sale):
        invoices = []
        for inv in sale.invoice_ids:
            if inv.type == 'out_invoice' and inv.state not in ['cancel', 'draft']:
                invoices.append(inv)
        if len(invoices) > 1:
            raise osv.except_osv(_('Error!'), _('There is more than one invoice associated with this order'))
        return invoices

    def _check_refund_account(self, sale):
        if not sale.shop_id.default_customer_account:
            raise osv.except_osv(_('Configuration Error'), _('Please define a payment account for this shop'))
        return sale.shop_id.default_customer_account.id

    def _cancel_pickings(self, cr, uid, sale, accept_done):
        wf_service = netsvc.LocalService("workflow")
        for pick in sale.picking_ids:
            if pick.state == 'cancel' or (accept_done and pick.state == 'done'):
                continue
            all_done = True
            for move in pick.move_lines:
                if move.state != 'done':
                    all_done = False
            if all_done:
                wf_service.trg_validate(uid, 'stock.picking', pick.id, 'button_done', cr)
            wf_service.trg_validate(uid, 'stock.picking', pick.id, 'button_cancel', cr)
            util.log(self, 'Cancelled picking %s, state %s' % (pick.name, pick.state), logging.INFO)
            
        sale.refresh()

        # Check if all picks are now cancelled
        for pick in sale.picking_ids:
            acceptable_states = ['draft', 'cancel']
            if accept_done:
                acceptable_states.append('done')
            if pick.state not in acceptable_states:
                raise osv.except_osv(
                    _('Could not cancel sale order'),
                    _('There was a problem cancelling the associated stock moves.'))

    def _refund_invoices(self, cr, uid, sale, invoices, refund_account_id):
        invoice_obj = self.pool.get('account.invoice')
        wf_service = netsvc.LocalService("workflow")

        for inv in invoices:
            if inv.type != 'out_invoice':
                continue
            # Generate refund
            refund_journal_ids = self.pool.get('account.journal').search(cr, uid, [('type','=','sale')])
            if refund_journal_ids:
                refund_journal_id = refund_journal_ids[0]
            else:
                refund_journal_id = None
            refund_id = invoice_obj.refund(cr, uid, [inv.id], description=False, journal_id=refund_journal_id)[0]
            # Confirm invoice
            invoice_obj.button_compute(cr, uid, [refund_id])
            wf_service.trg_validate(uid, 'account.invoice', refund_id, 'invoice_open', cr)
            refund = invoice_obj.browse(cr, uid, refund_id)
            if inv.payment_ids:
                # Generate refund accounting move
                payment = inv.payment_ids[0]
                refund_account_id = payment.account_id.id
                refund_journal_id = payment.journal_id.id
            else:
                ids = self.pool.get('account.journal').search(cr, uid, [('default_debit_account_id','=',refund_account_id)])
                if not ids:
                    raise osv.except_osv(
                        _('Could not cancel sale order'),
                        _('Could not find a journal for the payment account.'))
                refund_journal_id = ids[0]

            invoice_obj.pay_and_reconcile(cr, uid, [refund.id], inv.amount_total, refund_account_id, refund.period_id.id,
                refund_journal_id, refund_account_id, refund.period_id.id, refund_journal_id)
            util.log(self, 'Created refund for sale order %s' % (sale.name), logging.INFO)
            break

    def refund(self, cr, uid, ids, description, cancel_assigned=False, accept_done=False, return_cois=False, context=None):
        for sale in self.browse(cr, uid, ids, context):
            self._refund_check_order(sale, cancel_assigned, accept_done)
            invoices = self._check_invoices(sale)
            self._cancel_pickings(cr, uid, sale, accept_done)
            if invoices:
                refund_account_id = self._check_refund_account(sale)
                self._refund_invoices(cr, uid, sale, invoices, refund_account_id)
            event_vals = {'subject': 'Sale Order Refunded: %s' % sale.name,
                      'body_text': 'Sale Order Refunded: %s' % sale.name,
                      'partner_id': sale.partner_id.id,
                      'date': time.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                      'model': 'sale.order',
                      'res_id': sale.id,
                      'user_id': uid,
                      'email_from': 'OpenERP <openerp@localhost>'}
            self.pool.get('mail.message').create(cr, uid, event_vals, context=context)
            self.pool.get('sale.order.line').write(cr, uid, [line.id for line in sale.order_line], {'state': 'cancel'})
            self.write(cr, uid, [sale.id], {'state': 'cancel'})
            util.log(self, 'Cancelled sale order %s' % sale.name, logging.INFO)

    def _refund(self, cr, uid, original, order, context):
        acc_move_line_obj = self.pool.get('account.move.line')
        
        # 1. Grab old invoice and payments
        old_invoices = [i for i in original.invoice_ids if i.type == 'out_invoice' and i.state not in ('cancel', 'draft')]
        
        if len(old_invoices) == 1:
            has_invoice = True
        elif len(old_invoices) == 0:
            has_invoice = False
        else:
            raise osv.except_osv(('Error!'),('Multiple Invoices to Refund'))
        
        # 2. Unreconcile old invoice
        if has_invoice:
            invoice_old = old_invoices[0]
            payments = [p for p in invoice_old.payment_ids]
            payment_ids = [p.id for p in payments]
            if payment_ids:
                p_acc_id = acc_move_line_obj.browse(cr, uid, payment_ids[0]).account_id.id
        
                recs = acc_move_line_obj.read(cr, uid, payment_ids, ['reconcile_id','reconcile_partial_id'])
                unlink_ids = []
                full_recs = filter(lambda x: x['reconcile_id'], recs)
                rec_ids = [rec['reconcile_id'][0] for rec in full_recs]
                part_recs = filter(lambda x: x['reconcile_partial_id'], recs) # Should not be partial - but for completeness it is included
                part_rec_ids = [rec['reconcile_partial_id'][0] for rec in part_recs]
                unlink_ids += rec_ids
                unlink_ids += part_rec_ids
                if len(unlink_ids):
                   self.pool.get('account.move.reconcile').unlink(cr, uid, unlink_ids)
        
        # 3. Refund with credit note and reconcile with origional invoice
        self.refund(cr, uid, [original.id], 'Edit Refund:%s' % original.name, context=context, accept_done=True, cancel_assigned=True)

        if has_invoice:
            # 4. Create a new invoice and find difference between this and existing payment(s)
            payment_credit = reduce(lambda x,y: x+(y.credit-y.debit), payments, 0.0)
            invoice_id = self.action_invoice_create(cr, uid, [order.id])
            invoice = self.pool.get('account.invoice').browse(cr, uid, [invoice_id], context=context)[0]
            wkf_service = netsvc.LocalService('workflow')
            wkf_service.trg_validate(uid, 'account.invoice', invoice.id, 'invoice_open', cr)
            if payment_ids:
                payment_ids.extend([pmnt.id for pmnt in invoice.move_id.line_id if pmnt.account_id.id == p_acc_id])
            payment_diff = invoice.amount_total - payment_credit
            
            # 5. If difference then generate a payment for the difference
            if payment_diff:
               voucher_id = self.generate_payment_with_pay_code(cr, uid, 'paypal_standard', order.partner_id.id, payment_diff, order.name, order.name, order.date_order, True, context)
               voucher = self.pool.get('account.voucher').browse(cr, uid, voucher_id)
               if payment_ids:
                   payment_ids.extend([pmnt.id for pmnt in voucher.move_id.line_id if pmnt.account_id.id == p_acc_id])
            
            # 6. Reconcile all payments with current invoice
            if payment_ids:
                acc_move_line_obj.reconcile(cr, uid, payment_ids, context=context)

    def _unreconcile_refund_and_cancel(self, cr, uid, original_id, order, context):
        if context == None:
            context = {}
        original = self.browse(cr, uid, original_id, context)
        try:
            self._refund(cr, uid, original, order, context)
        except osv.except_osv, e:
            raise osv.except_osv('Error while refunding %s' % original.name, e.value)

    def get_edit_original(self, cr, uid, order, context):
        if order.origin:
            original_ids = self.search(cr, uid, [('name', '=', order.origin)], context)
            if len(original_ids) == 1:
                return original_ids[0]
            elif len(original_ids) == 0:
                return False
            else:
                raise osv.except_osv('Found multiple sale orders with origin %s, must only be to edit.' % order.origin)
        else:
            return False

    def action_ship_create(self, cr, uid, ids, context=None):
        # run on order confirm, after action_wait

#        # Sale order edit
#        # -  pre-action hook: find what has been edited
#        line_moves = self.check_consolidation(cr, uid, ids, context)

        # -    action: run original action
        res = super(sale_order, self).action_ship_create(cr, uid, ids, context)

#        # - post-action hook: replace new stuff generated in the action with old stuff
#        self._fixup_created_picking(cr, uid, line_moves, context)

        for order in self.browse(cr, uid, ids, context):
            original_id = self.get_edit_original(cr, uid, order, context) 
            if original_id:
                self._unreconcile_refund_and_cancel(cr, uid, original_id, order, context)
            
        return res

sale_order()


class sale_order_line(osv.osv):
    _inherit = 'sale.order.line'
    
    _columns = {
        'order_edit_original_line_id': fields.many2one('sale.order.line', 'Order Edit Original Line',
                                                    help='A reference to the line this was copied from, if any'), 
    }

    def copy_data(self, cr, uid, id_, default=None, context=None):
        if context and context.get('order_edit'):
            if not default:
                default = {}
            default['order_edit_original_line_id'] = id_
        return super(sale_order_line, self).copy_data(cr, uid, id_, default, context)


sale_order_line()

