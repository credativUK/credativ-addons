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

from osv import orm, osv, fields
import netsvc
from tools.translate import _

import re
import itertools
from collections import defaultdict

class OrderEdit(object):

    def _consolidate_edit_lines(self, cr, uid, original, order, context=None, non_consolidable_fields=None, fields_noted_for_fixup=None):
        """
        Given an original order, and an edit order:
         * Check that no done lines are reduced.
         * Remove all lines from the edit order.
         * Recreate up to two lines for each product:
           - one for shipped items, and
           - one for unshipped items
         * Return a list of done lines.
        """
        done_totals = {}
        moves = []
        done_states = ['done']
        key2old_lines = defaultdict(lambda : defaultdict(dict))
        new_id2old_lines = {}

        if self._name == 'sale.order':
            done_states.append('assigned')

        if non_consolidable_fields is None:
            non_consolidable_fields = set()

        if fields_noted_for_fixup is None:
            fields_noted_for_fixup = set()

        def _list_browse_to_id(l):
            l = l[:]
            for i in range(len(l)):
                if isinstance(l[i], orm.browse_record):
                    l[i] = l[i].id
                elif isinstance(l[i], orm.browse_null):
                    l[i] = False
                elif isinstance(l[i], list):
                    l[i] = tuple(_list_browse_to_id(l[i]))
            return l

        for picking in original.picking_ids:
            for move in picking.move_lines:
                moves.append(move)
                if move.state in done_states:
                    if self._name == 'sale.order':
                        tax = tuple([x.id for x in move.sale_line_id.tax_id])
                        discount = move.sale_line_id.discount
                        key = [move.product_id, move.sale_line_id.price_unit, tax, discount]
                    else:
                        tax = tuple([x.id for x in move.purchase_line_id.taxes_id])
                        discount = 0
                        key = [move.product_id, move.purchase_line_id.price_unit, tax, discount]

                    # Extend key to discriminate between differing non-consolidable values
                    line = self._name == 'sale.order' and move.sale_line_id or move.purchase_line_id
                    key_additional = [getattr(line, field) for field in non_consolidable_fields]
                    key_additional = _list_browse_to_id(key_additional)
                    key.append(tuple(key_additional))

                    key = tuple(key)
                    done_totals[key] = done_totals.setdefault(key, 0) + move.product_qty

        # Get a list of lines for each product in the edit sale order
        edit_totals = {}
        for line in order.order_line:
            if line.product_id.id == False or line.product_id.type == 'service':
                continue
            if self._name == 'sale.order':
                qty = line.product_uom_qty
                tax = tuple([x.id for x in line.tax_id])
                discount = line.discount
            else:
                qty = line.product_qty
                tax = tuple([x.id for x in line.taxes_id])
                discount = 0
            key = [line.product_id, line.price_unit, tax, discount]

            # Extend key to discriminate between differing non-consolidable values
            key_additional = [getattr(line, field) for field in non_consolidable_fields]
            key_additional = _list_browse_to_id(key_additional)
            key.append(tuple(key_additional))

            key = tuple(key)
            edit_totals[key] = edit_totals.setdefault(key, 0) + qty

            # Retain requested line data for reference during fixup after records have been unlinked.
            # TODO: Could allow fields_noted_for_fixup to be a list of functions for greater adaptability.
            key2old_lines[key][line.id].update({f:getattr(line,f) for f in fields_noted_for_fixup})

        # Check that the totals in the edit aren't less than the shipped qty
        for (product, price_unit, tax, discount, preserve_vals), done_total in done_totals.iteritems():
            if edit_totals.get((product, price_unit, tax, discount, preserve_vals), 0) < done_total:
                raise osv.except_osv(_('Error !'),
                                     _('There must be at least %d of %s in'
                                       ' the edited order with unit price %s'
                                       ' and taxes %s and discount %s, as they have'
                                       ' already been assigned or shipped.'
                                            % (done_total, product.name, price_unit, tax, discount)))

        new_vals = {}
        for line in order.order_line:
            if line.product_id.id == False or line.product_id.type == 'service':
                continue
            new_vals[(line.product_id.id, line.price_unit)] = {'price_unit': line.price_unit}
            if self._name == 'purchase.order':
                new_vals[(line.product_id.id, line.price_unit)].update({'date_planned': line.date_planned})
                line.write({'state': 'cancel'}, context=context)
            if self._name == 'sale.order':
                new_vals[(line.product_id.id, line.price_unit)].update({'type': line.type})
                line.button_cancel(context=context)
            line.unlink(context=context)

        def add_product_order_line(product_id, price_unit, qty, tax, discount):
            line_obj = self.pool.get(order.order_line[0]._name)
            product = self.pool.get('product.product').browse(cr, uid, product_id, context=context)

            #type: make_to_stock is default in sale.order.line
            vals = {'order_id': order.id,
                    'name': product.name,
                    'product_id': product.id,
                    'product_uom': product.uom_id.id,
                    }

            if self._name == 'sale.order':
                vals.update({'product_uom_qty': qty})
                vals.update({'tax_id': [[6, 0, tax]]})
                vals.update({'discount': discount})
            else:
                vals.update({'product_qty': qty})
                vals.update({'taxes_id': [[6, 0, tax]]})
                #vals.update({'discount': discount}) # TODO: Compatibility with purchase_discount module

            vals.update(new_vals.get((product.id, price_unit), {}))

            line_id = line_obj.create(cr, uid, vals, context=context)
            if self._name == 'sale.order':
                line_obj.browse(cr, uid, line_id, context=context).button_confirm()
            return line_id

        line_moves = defaultdict(list)
        other_moves = defaultdict(list)
        for m in moves:
            if self._name == 'sale.order':
                price_unit = m.sale_line_id.price_unit
                tax = tuple([x.id for x in m.sale_line_id.tax_id])
                discount = m.sale_line_id.discount
            else:
                price_unit = m.purchase_line_id.price_unit
                tax = tuple([x.id for x in m.purchase_line_id.taxes_id])
                discount = 0
            if m.state in done_states:
                line_id = add_product_order_line(m.product_id.id, price_unit, m.product_qty, tax, discount)
                line_moves[line_id].append(m)
            else:
                other_moves[(m.product_id.id, price_unit, discount)].append(m)

        remain_moves = {}
        for key, edit_total in edit_totals.iteritems():
            (product, price_unit, tax, discount, preserved_fields) = key
            remainder = edit_total - done_totals.get((product, price_unit, tax, discount, preserved_fields), 0)
            if remainder > 0:
                line_id = add_product_order_line(product.id, price_unit, remainder, tax, discount)
                new_id2old_lines.update({line_id : key2old_lines.get(key)})
                remain_moves[line_id] = other_moves[(product.id, price_unit, tax, discount)]

        self._fixup_consolidated_lines(cr, uid, order, new_id2old_lines, context=context)

        return line_moves, remain_moves

    def check_consolidation(self, cr, uid, ids, context=None):
        # TODO: edit with available moves
        # move may be made available after the initial copy so can't give a warning then
        # need to change confirm button to run an action that warns user of the available move
        # and then trigger the workflow to continue the current behaviour
        line_moves = None
        remain_moves = None
        for order in self.browse(cr, uid, ids, context=context):
            if order.order_edit_id:
                line_moves, remain_moves = self._consolidate_edit_lines(cr, uid, order.order_edit_id, order, context=context)
        return line_moves, remain_moves

    def _fixup_consolidated_lines(self, cr, uid, order, preserved_fields, context=None):
        ''' Hook point for amending lines post-consolidation
            @param order: Browse record of order edit
            @param preserved_fields: Dict mapping consolidated line ids to selected
                                     field values of old ids. Fields selected with
                                     fields_noted_for_fixup passed to _consolidate_edit_lines()
        '''
        return

    def copy_for_edit(self, cr, uid, id_, context=None):
        if context is None:
            context = {}
        context = context.copy()
        context['order_edit'] = True
        try:
            if len(id_) == 1:
                id_ = id[0]
        except TypeError:
            pass
        order = self.browse(cr, uid, id_, context=context)

        order_states = {
            'sale.order':     ('progress','manual'),
            'purchase.order': ('confirmed','approved'),
            }

        if order.state in order_states[self._name]:
            new_id = self.copy(cr, uid, id_, default={'order_edit_id': order.id}, context=context)
            original_order_name = re.sub('-edit[0-9]+$', '', order.name)
            similar_name_ids = self.search(cr, uid, [('name', 'like', original_order_name + '%')], context=context)
            similar_names = set(similar_order['name'] for similar_order in self.read(cr, uid, similar_name_ids, ['name'], context=context))
            for i in itertools.count(1):
                new_name = '%s-edit%d' % (original_order_name, i)
                if new_name not in similar_names:
                    break
            vals = {'name': new_name, 'order_edit_id': order.id}

            self.write(cr, uid, new_id, vals, context=context)

            self.message_post(cr, uid, [id_], body=_('Order has been copied to be edited in order %s') % (new_name,), context=context)
            return new_id
        else:
            raise osv.except_osv(_('Error!'), _('Only able to edit orders which are in progress.'))

    def _cancel_pickings(self, cr, uid, order, accept_done, context=None):
        wf_service = netsvc.LocalService("workflow")
        for pick in order.picking_ids:
            if pick.state == 'cancel' or (accept_done and pick.state == 'done'):
                continue
            all_done = True
            for move in pick.move_lines:
                if move.state != 'done':
                    all_done = False
            if all_done:
                wf_service.trg_validate(uid, 'stock.picking', pick.id, 'button_done', cr)
            wf_service.trg_validate(uid, 'stock.picking', pick.id, 'button_cancel', cr)
            #Call work flow twice to cancel stock picking
            wf_service.trg_validate(uid, 'stock.picking', pick.id, 'button_cancel', cr)
            self.message_post(cr, uid, [order.id], body=_('Cancelled picking %s in state %s due to order edit') % (pick.name, pick.state,), context=context)

        order.refresh()

        # Check if all picks are now cancelled
        for pick in order.picking_ids:
            acceptable_states = ['draft', 'cancel']
            if accept_done:
                acceptable_states.append('done')
            if pick.state not in acceptable_states:
                raise osv.except_osv(
                    _('Could not cancel order'),
                    _('There was a problem cancelling the associated stock moves.'))

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
