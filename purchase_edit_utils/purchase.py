# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 credativ ltd (<http://www.credativ.co.uk>). All Rights Reserved
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

import logging

from osv import osv, fields
from openerp.tools.translate import _
from openerp.osv.orm import browse_record, browse_null

_logger = logging.getLogger(__name__)

class PurchaseOrder(osv.Model):
    _inherit = 'purchase.order'

    def allocate_check_restrict(self, cr, uid, ids, context=None):
        if context == None:
            context = {}
        states = ['done']
        if not context.get('psa_po_cancel'):
            states.append('cancel')
        restricted_ids = []
        for purchase in self.browse(cr, uid, ids, context=context):
            if purchase.state in states:
                restricted_ids.append(purchase.id)
            for line in purchase.order_line:
                if line.state in states:
                    restricted_ids.append(purchase.id)
                if not context.get('psa_skip_moves'):
                    for move in line.move_ids:
                        if move.state in states:
                            restricted_ids.append(purchase.id)
        return list(set(restricted_ids))

class PurchaseOrderLine(osv.Model):
    _inherit = 'purchase.order.line'

    def do_split(self, cr, uid, id, qty, context=None):
        purchase_obj = self.pool.get('purchase.order')
        move_obj = self.pool.get('stock.move')
        line = self.browse(cr, uid, id, context=context)
        new_line_id = False
        if line.product_qty > qty:
            orig_moves = [m.id for m in line.move_ids]
            move_states = list(set([m.state for m in line.move_ids]))
            if len(move_states) == 1:
                move_state = move_states[0]
            elif len(move_states) > 1:
                raise osv.except_osv(_('Error!'),_('Unable to split purchase line %s when it has a combination of moves in different states: %s') % (line.id, move_states))
            self.write(cr, uid, [line.id], {'product_qty': qty}, context=context)
            new_line_id = self.copy(cr, uid, line.id, {'product_qty': line.product_qty - qty}, context=context)
            self.write(cr, uid, [new_line_id], {'state': line.state}, context=context)
            if line.state not in ('draft', 'cancel'):
                line = self.browse(cr, uid, line.id, context=context)
                if orig_moves:
                    move_id = move_obj.create(cr, uid, purchase_obj._prepare_order_line_move(cr, uid, line.order_id, line, line.order_id.picking_ids[0].id, context=context))
                    move_obj.write(cr, uid, [move_id,], {'state': move_state}, context=context)
                    new_line = self.browse(cr, uid, new_line_id, context=context)
                    move_id = move_obj.create(cr, uid, purchase_obj._prepare_order_line_move(cr, uid, new_line.order_id, new_line, new_line.order_id.picking_ids[0].id, context=context))
                    move_obj.write(cr, uid, [move_id,], {'state': move_state}, context=context)
            if orig_moves:
                move_obj.write(cr, uid, orig_moves, {'move_dest_id': False, 'purchase_line_id': False, 'picking_id': False}, context=context)
                move_obj.action_cancel(cr, uid, orig_moves, context=context)
        elif line.product_qty < qty:
            raise osv.except_osv(_('Error!'),_('Unable to split purchase line into a greater quantity than it has'))
        return line.id, new_line_id

    def do_merge(self, cr, uid, ids, context=None):
        def make_key(br, fields): # Copied from module purchase function do_merge
            list_key = []
            for field in fields:
                field_val = getattr(br, field)
                if field in ('product_id', 'move_dest_id', 'account_analytic_id'):
                    if not field_val:
                        field_val = False
                if isinstance(field_val, browse_record):
                    field_val = field_val.id
                elif isinstance(field_val, browse_null):
                    field_val = False
                elif isinstance(field_val, list):
                    field_val = ((6, 0, tuple([v.id for v in field_val])),)
                list_key.append((field, field_val))
            list_key.sort()
            return tuple(list_key)

        purchase_obj = self.pool.get('purchase.order')
        move_obj = self.pool.get('stock.move')

        order_infos = {}
        for order_line in self.browse(cr, uid, ids, context=context):
            if order_line.state == 'done':
                continue
            line_key = make_key(order_line, ('taxes_id', 'price_unit', 'product_id', 'move_dest_id', 'account_analytic_id'))
            o_line = order_infos.setdefault(line_key, {})
            if o_line:
                # merge the line with an existing line
                o_line['product_qty'] += order_line.product_qty * order_line.product_uom.factor / o_line['uom_factor']
                o_line['orig_line_ids'].append(order_line.id)
                o_line['count'] += 1
            else:
                # append a new "standalone" line
                for field in ('product_qty', 'product_uom'):
                    field_val = getattr(order_line, field)
                    if isinstance(field_val, browse_record):
                        field_val = field_val.id
                    o_line[field] = field_val
                o_line['uom_factor'] = order_line.product_uom and order_line.product_uom.factor or 1.0
                o_line['orig_line_ids'] = [order_line.id,]
                o_line['state'] = order_line.state
                o_line['count'] = 1

        for order_line in order_infos.values():
            if order_line['count'] == 1:
                continue
            del order_line['uom_factor']
            if len(order_line['orig_line_ids']) > 1:
                # Cancel old moves
                orig_moves = move_obj.search(cr, uid, [('purchase_line_id', 'in', order_line['orig_line_ids'])], context=context)
                move_states = list(set([m['state'] for m in move_obj.read(cr, uid, orig_moves, ['state'], context=context)]))
                if len(move_states) == 1:
                    move_state = move_states[0]
                elif len(move_states) > 1:
                    _logger.warning(_('Unable to merge purchase lines %s when it has a combination of moves in different states: %s') % ( order_line['orig_line_ids'], move_states))
                    continue
                # Create new move and cancel old PO lines
                first = True
                for line in self.browse(cr, uid, order_line['orig_line_ids'], context=context):
                    if first:
                        first = False
                        self.write(cr, uid, [line.id], {'product_qty': order_line['product_qty']}, context=context)
                        if orig_moves:
                            move_id = move_obj.create(cr, uid, purchase_obj._prepare_order_line_move(cr, uid, line.order_id, line, line.order_id.picking_ids[0].id, context=context))
                            move_obj.write(cr, uid, [move_id,], {'state': move_state}, context=context)
                    else:
                        self.write(cr, uid, [line.id], {'state': 'cancel'}, context=context)
                        self.unlink(cr, uid, [line.id], context=context)
                if orig_moves:
                    move_obj.action_cancel(cr, uid, orig_moves, context=context)
                    move_obj.write(cr, uid, orig_moves, {'move_dest_id': False, 'purchase_line_id': False, 'picking_id': False}, context=context)

    def _generate_purchase_line(self, cr, uid, product_id, qty, pricelist_id, partner_id, schedule_date, context=None):
        # Generate a new PO line values
        if context == None:
            context = {}

        picking_obj = self.pool.get('stock.picking.in')
        purchase_obj = self.pool.get('purchase.order')
        purchase_line_obj = self.pool.get('purchase.order.line')
        product_obj = self.pool.get('product.product')
        partner_obj = self.pool.get('res.partner')
        pricelist_obj = self.pool.get('product.pricelist')

        partner = partner_obj.browse(cr, uid, partner_id, context=context)
        new_context = context.copy()
        new_context.update({'lang': partner.lang, 'partner_id': partner.id})
        product = product_obj.browse(cr, uid, product_id, context=new_context)
        pricelist = pricelist_obj.browse(cr, uid, pricelist_id, context=context)
        price = pricelist.price_get(product.id, qty, partner.id)

        name = product.partner_ref
        if product.description_purchase:
            name += '\n'+ product.description_purchase
        line_vals = {
            'name': name,
            'product_qty': qty,
            'product_id': product.id,
            'product_uom': product.uom_po_id.id,
            'price_unit': price or 0.0,
            'date_planned': schedule_date
        }

        product_change_vals = purchase_line_obj.onchange_product_id(cr, uid, [], pricelist_id=pricelist.id, product_id=line_vals['product_id'],
            qty=line_vals['product_qty'], uom_id=line_vals['product_uom'], partner_id=partner.id,
            fiscal_position_id=partner.property_account_position and partner.property_account_position.id,
            date_planned=line_vals['date_planned'], name=line_vals['name'], price_unit=line_vals['price_unit'], context=context)
        for key, value in product_change_vals.get('value', {}).iteritems():
            if value and type(value) in (tuple, list):
                if type(value[0]) is dict:
                    line_vals[key] = [(0, 0, d) for d in value]
                elif type(value[0]) in (int, long):
                    line_vals[key] = [(6, 0, value)]
                else:
                    line_vals[key] = value
            else:
                line_vals[key] = value

        return line_vals

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
