# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 credativ Ltd (<http://credativ.co.uk>).
#    All Rights Reserved
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from osv import osv, fields
from tools.translate import _
import netsvc
from openerp.addons.base_order_edit.order_edit import OrderEdit

class SaleOrder(osv.osv, OrderEdit):
    _inherit = 'sale.order'

    _columns = {
        'order_edit_id': fields.many2one('sale.order', 'Edit of Order', readonly=True),
    }

    def action_run_order_edit(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        if not ids:
            return {}
        oe_obj = self.pool.get('sale.order.edit_wizard')

        context.update({'active_id': ids[0], 'active_ids': [ids[0]]})
        oe_id = oe_obj.create(cr, uid, {}, context=context)
        return oe_obj.edit_order(cr, uid, [oe_id], context=context)

    def copy_data(self, cr, uid, id_, default=None, context=None):
        if not default:
            default = {}
        if 'order_edit_id' not in default:
            default['order_edit_id'] = False
        default['workflow_process_id'] = False
        return super(SaleOrder, self).copy_data(cr, uid, id_, default, context=context)

    def action_ship_create(self, cr, uid, ids, context=None):
        line_moves, remain_moves = self.check_consolidation(cr, uid, ids, context)
        res = super(SaleOrder, self).action_ship_create(cr, uid, ids, context=context)
        self._fixup_created_picking(cr, uid, line_moves, remain_moves, context)
        for order in self.browse(cr, uid, ids, context=context):
            if order.order_edit_id:
                self._refund(cr, uid, order.order_edit_id, order, context=context)
        return res

    def _refund_check_order(self, sale, cancel_assigned, accept_done, context=None):
        if sale.state not in ('progress', 'manual'):
            raise osv.except_osv(_('Error!'), _('Sale order being edited should be in progress.'))
        for pick in sale.picking_ids:
            if not cancel_assigned and pick.state == 'assigned':
                raise osv.except_osv(_('Error!'),
                    _('Unable to edit order, stock has already been assigned - please cancel pickings manually'))
            if not accept_done and pick.state == 'done':
                raise osv.except_osv(_('Error!'),
                    _('Unable to edit order, stock has already been shipped - please process manually'))

    def _refund_invoices(self, cr, uid, sale, context=None):
        invoice_obj = self.pool.get('account.invoice')
        wf_service = netsvc.LocalService("workflow")
        res = []
        for inv in sale.invoice_ids:
            if not (inv.type == 'out_invoice' and inv.state not in ['cancel', 'draft']):
                continue

            # Generate and confirm refund using the default sale refund journal
            refund_id = invoice_obj.refund(cr, uid, [inv.id], description=False, journal_id=None, context=context)[0]
            invoice_obj.button_compute(cr, uid, [refund_id], context=context)
            wf_service.trg_validate(uid, 'account.invoice', refund_id, 'invoice_open', cr)

            refund = invoice_obj.browse(cr, uid, [refund_id], context=context)[0]
            move_line_ids = []
            move_line_ids.extend([move_line.id for move_line in inv.move_id.line_id if move_line.account_id.id == inv.account_id.id])
            move_line_ids.extend([move_line.id for move_line in refund.move_id.line_id if move_line.account_id.id == refund.account_id.id])
            if len(move_line_ids) > 0:
                self.pool.get('account.move.line').reconcile(cr, uid, move_line_ids)

            res.append(refund_id)

    def _cancel_mo(self, cr, uid, order, context=None):
        '''Cancel Manufacturing Order'''
        if context is None:
            context={}
        mo_pool = self.pool.get('mrp.production')
        # FIXME: There are better ways of finding linked MOs, eg thorugh procurements
        mo_ids = mo_pool.search(cr,uid,[('origin','=',order.name), ('state','!=','cancel')],context=context)
        wf_service = netsvc.LocalService("workflow")
        # Cancel Picking for MO which are not in (done,in_production) state. If MO are in (done,in_production)state then move MO to edited order.
        if mo_ids:
            try:
                self.pool.get('mrp.production').action_cancel(cr,uid,mo_ids,context=context)
                proc_pool = self.pool.get('procurement.order')
                # Run schedule to create new Manufacturing order
                proc_pool.run_scheduler(cr,uid,False,False,context=context)
            except Exception, e:
                raise osv.except_osv(_('Error!'),_('Error cancelling manufacturing order: ') + e.value)

    def refund(self, cr, uid, ids, description, cancel_assigned=False, accept_done=False, return_cois=False, context=None):
        wf_service = netsvc.LocalService("workflow")
        res = {}
        for sale in self.browse(cr, uid, ids, context=context):
            self._refund_check_order(sale, cancel_assigned, accept_done, context=context)
            self._cancel_pickings(cr, uid, sale, accept_done, context=context)
            res[sale.id] = self._refund_invoices(cr, uid, sale, context=context)
            self.pool.get('sale.order.line').write(cr, uid, [line.id for line in sale.order_line], {'state': 'cancel'}, context=context)
            self.write(cr, uid, [sale.id], {'state': 'cancel'}, context=context)
            wf_service.trg_write(uid, 'sale.order', sale.id, cr)
            self.message_post(cr, uid, [sale.id], body=_('Sale order %s refunded and cancelled due to order edit') % (sale.name,), context=context)
        return res

    def _refund(self, cr, uid, original, order, context=None):
        wkf_service = netsvc.LocalService('workflow')
        acc_move_line_obj = self.pool.get('account.move.line')

        # 1. Find old invoice and payments
        old_invoices = [i for i in original.invoice_ids if i.type == 'out_invoice' and i.state not in ('cancel', 'draft')]

        # 2. Unreconcile old invoices
        all_payments = []
        all_payment_ids = []
        p_acc_id = False
        for invoice_old in old_invoices:
            payments = [p for p in invoice_old.payment_ids]
            payment_ids = [p.id for p in payments]
            all_payments.extend(payments)
            if payment_ids:
                p_acc_id = acc_move_line_obj.browse(cr, uid, payment_ids[0], context=context).account_id.id

                recs = acc_move_line_obj.read(cr, uid, payment_ids, ['reconcile_id','reconcile_partial_id'], context=context)
                unlink_ids = []
                full_recs = filter(lambda x: x['reconcile_id'], recs)
                rec_ids = [rec['reconcile_id'][0] for rec in full_recs]
                part_recs = filter(lambda x: x['reconcile_partial_id'], recs) # Should not be partial - but for completeness it is included
                part_rec_ids = [rec['reconcile_partial_id'][0] for rec in part_recs]
                unlink_ids += rec_ids
                unlink_ids += part_rec_ids
                if len(unlink_ids):
                    self.pool.get('account.move.reconcile').unlink(cr, uid, unlink_ids, context=context)
        all_payment_ids = [p.id for p in all_payments]

        # 3. Refund with credit note and reconcile with origional invoice
        self.refund(cr, uid, [original.id], 'Edit Refund:%s' % original.name, accept_done=True, cancel_assigned=True, context=context)

        if old_invoices:
            # 4. Create a new invoice and find difference between this and existing payment(s)
            payment_credit = reduce(lambda x,y: x+(y.credit-y.debit), all_payments, 0.0)
            wkf_service.trg_validate(uid, 'sale.order', order.id, 'manual_invoice', cr)
            order.refresh()
            assert(len(order.invoice_ids) == 1)
            invoice = order.invoice_ids[0]
            wkf_service.trg_validate(uid, 'account.invoice', invoice.id, 'invoice_open', cr)
            if all_payment_ids:
                all_payment_ids.extend([pmnt.id for pmnt in invoice.move_id.line_id if pmnt.account_id.id == p_acc_id])

            # 5. If difference then generate a payment for the difference
            # Deprecated - payments should not be automatically created, only the credit notes/new invoice affecting payables and receivables

            # 6. Reconcile all payments with current invoice
            if all_payment_ids:
                acc_move_line_obj.reconcile_partial(cr, uid, all_payment_ids, context=context)

        # 7. Cancel draft invoices
        draft_invoice_ids = [i.id for i in original.invoice_ids if i.type == 'out_invoice' and i.state == 'draft']
        for draft_invoice_id in draft_invoice_ids:
            wkf_service.trg_validate(uid, 'account.invoice', draft_invoice_id, 'invoice_cancel', cr)

        # 8 Cancel MO,create new MO and run procurement scheduler
        if self.pool.get('mrp.production'):
            self._cancel_mo(cr, uid, original, context=context)

        # 9 Cancel the old order
        wkf_service.trg_validate(uid, 'sale.order', original.id, 'cancel', cr)
        wkf_service.trg_validate(uid, 'sale.order', original.id, 'invoice_cancel', cr)
        wkf_service.trg_validate(uid, 'sale.order', original.id, 'ship_cancel', cr)

        return True

    def _fixup_created_picking(self, cr, uid, line_moves, remain_moves, context):
        # This is a post confirm hook
        # - post-action hook: replace new stuff generated in the action with old stuff
        # identified in the pre-action hook
        move_pool = self.pool.get('stock.move')
        pick_pool = self.pool.get('stock.picking')
        line_pool = self.pool.get('sale.order.line')
        proc_pool = self.pool.get('procurement.order')
        wf_service = netsvc.LocalService("workflow")

        if line_moves is not None:
            for line_id, old_moves in line_moves.iteritems():
                line = line_pool.browse(cr, uid, line_id)
                created_moves = [x for x in line.move_ids]
                for old_move in old_moves:
                    try:
                        created_move = created_moves.pop()
                    except IndexError:
                        raise osv.except_osv(_('Error!'), _('The edited order must include any done or assigned moves'))
                    # Move old stock_move and stock_picking to new order
                    picking = created_move.picking_id
                    move_pool.write(cr, uid, [old_move.id], {'sale_line_id': line_id})
                    pick_pool.write(cr, uid, old_move.picking_id.id, {'sale_id':line.order_id.id})
                    proc_ids = proc_pool.search(cr, uid, [('move_id', '=', old_move.id), ('state', 'not in', ('cancel',))], context=context)
                    line_pool.write(cr, uid, [line.id,], {'procurement_id': proc_ids and proc_ids[0] or False}, context=context)
                    # Cancel and remove new replaced stock_move and stock_picking
                    move_pool.write(cr, uid, created_move.id, {'sale_line_id': False, 'picking_id': False})
                    created_move.action_cancel()
                    picking.refresh()
                    if not picking.move_lines:
                        pick_pool.write(cr, uid, picking.id, {'sale_id': False})
                        wf_service.trg_validate(uid, 'stock.picking', picking.id, 'button_cancel', cr)
                        wf_service.trg_validate(uid, 'stock.picking', picking.id, 'button_cancel', cr)
                        pick_pool.action_cancel(cr, uid, [picking.id])
                line = line_pool.browse(cr, uid, line_id)
                if line.move_ids and all([move.state in ('done', 'cancel') for move in line.move_ids]):
                    line_pool.write(cr, uid, [line.id], {'state': 'done'}, context=context)
                assert(len(created_moves) == 0)

        if remain_moves is not None:
            picking = None
            old_picking_copy = None
            for line_id, old_moves in remain_moves.iteritems():
                line = self.pool.get('sale.order.line').browse(cr, uid, line_id)
                created_moves = [x for x in line.move_ids]
                if not picking and not old_picking_copy:
                    picking = old_moves and old_moves[0].picking_id or None
                    if picking:
                        old_picking_copy = pick_pool.copy(cr, uid, picking.id, {'move_lines': [], 'sale_id': line.order_id.id, 'name': '/'})
                if not old_picking_copy or not created_moves:
                    continue
                for created_move in created_moves:
                    new_picking = created_move.picking_id
                    move_pool.write(cr, uid, created_move.id, {'sale_line_id': line_id, 'picking_id': old_picking_copy})
                    new_picking.refresh()
                    if not new_picking.move_lines:
                        pick_pool.write(cr, uid, new_picking.id, {'sale_id': False})
                        wf_service.trg_validate(uid, 'stock.picking', new_picking.id, 'button_cancel', cr)
                        wf_service.trg_validate(uid, 'stock.picking', new_picking.id, 'button_cancel', cr)
                        pick_pool.action_cancel(cr, uid, [new_picking.id])
            if old_picking_copy:
                wf_service.trg_validate(uid, 'stock.picking', old_picking_copy, 'button_confirm', cr)
            # Old confirmed moves get canceled during refund

        return True

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
