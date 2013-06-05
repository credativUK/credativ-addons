# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2013 credativ Ltd (<http://credativ.co.uk>).
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

from osv import osv, fields
import re
import itertools
import netsvc

class sale_order_line(osv.osv):
    _inherit = 'sale.order.line'
    
    _columns = {
        'original_line_id': fields.many2one('sale.order.line', String='Original Order Line', help='The current order line is an edit for this order line', readonly=True,),
        'original_done': fields.boolean('Original Done', help='All moves for the original order line are done and cannot be edited', readonly=True,)
    }

    def copy_data(self, cr, uid, id, default=None, context=None):
        if not default:
            default = {}
        if context and context.get('order_edit'):
            default['original_line_id'] = id
        else:
            default['original_line_id'] = False
        res = super(sale_order_line, self).copy_data(cr, uid, id, default, context)
        if default.get('original_done', False): # Has to be done here since the super copy_data forces state to draft
            res['state'] = 'confirmed'
        return res

    def unlink(self, cr, uid, ids, context=None):
        for line in self.browse(cr, uid, ids, context=context):
            if line.original_done and line.order_id.state == 'draft':
                raise osv.except_osv('Could not remove order line', 'Edited order line is completed and cannot be deleted. Cancel the order edit instead.')
            elif line.original_done:
                raise osv.except_osv('Could not remove order line', 'Edited order line is completed and cannot be deleted.')
        return super(sale_order_line, self).unlink(cr, uid, ids, context=context)

sale_order_line()

class sale_order(osv.osv):
    _inherit = 'sale.order'

    _columns = {
            'original_order': fields.many2one('sale.order', string='Original Order', help='The current order is an edit for this order', readonly=True,),
            'edited_order': fields.many2one('sale.order', string='Edit Order', help='The current order is superseded by this order', readonly=True,),
        }

    def action_cancel_draft(self, cr, uid, ids, *args):
        res = super(sale_order, self).action_cancel_draft(cr, uid, ids, *args)

        for order in self.browse(cr, uid, ids):
            if order.edited_order:
                raise osv.except_osv('Could not set order to draft', 'This order has been superseded by an edit and cannot be reopened.')
            if order.original_order:
                try:
                    self.validate_for_edit(cr, uid, [order.original_order.id,])
                except osv.except_osv, e:
                    raise osv.except_osv('Could not set order to draft', 'This order has been superseded by an edit and cannot be reopened.')

        return res

    def validate_for_edit(self, cr, uid, ids, context=None):
        if not isinstance(ids, (list, tuple)):
            ids = [ids,]
        for order in self.browse(cr, uid, ids, context=context):
            if order.state not in ('progress', 'manual'):
                raise osv.except_osv('Could not edit order', 'Original should be in progress.')
            if order.edited_order:
                raise osv.except_osv('Could not edit order', 'This order has been superseded by an edit and cannot be reopened.')
            other_edits = self.search(cr, uid, [('state', 'in', ('draft', 'progress', 'manual')), ('original_order', '=', order.id)], count=True, context=context)
            if other_edits > context.get('validate_edit_confirm', False) and 1 or 0:
                raise osv.except_osv('Could not edit order', 'There are other edits for this order in draft or progress. Cancel them first.')
            if order.order_policy == 'prepaid':
                raise osv.except_osv('Could not edit order', 'Prepaid orders cannot be edited.')
            if order.order_policy != 'picking':
                raise osv.except_osv('Could not edit order', 'Only orders which are invoiced from pickings are supported.')
        return

    def copy_for_edit(self, cr, uid, id, context=None):
        if context is None:
            context = {}

        if isinstance(id, (list, tuple)):
            if len(id) != 1:
                # This is more of a coding error since the calling function should itterate over ids if more than one
                raise osv.except_osv('Could not copy order', 'Only one order can be copied for edit at a time')
            else:
                id = id[0]

        ctx = context.copy()
        ctx['order_edit'] = True

        order = self.browse(cr, uid, id, context=ctx)

        # Validate the order can be edited
        self.validate_for_edit(cr, uid, [order.id,], context=context)

        # Duplicate
        new_id = self.copy(cr, uid, order.id, context=ctx)
        # Split SO lines into shipped (readonly) and editable
        self.split_lines_for_edit(cr, uid, new_id, context=None)

        # Assign new -edit name and link to original order
        original_order_name = re.sub('-edit[0-9]+$', '', order.name)
        similar_name_ids = self.search(cr, uid, [('name', 'like', original_order_name + '%')])
        similar_names = set(similar_order['name'] for similar_order in self.read(cr, uid, similar_name_ids, ['name']))
        for i in itertools.count(1):
            new_name = '%s-edit%d' % (original_order_name, i)
            if new_name not in similar_names:
                break
        vals = {'name': new_name, 'original_order': order.id}
        self.write(cr, uid, new_id, vals)

        return new_id

    def split_lines_for_edit(self, cr, uid, id, context=None):
        sol_obj = self.pool.get('sale.order.line')

        order = self.browse(cr, uid, id, context=context)
        for line in order.order_line:
            if line.original_line_id:
                moves_done = []
                moves_other = []
                for move in line.original_line_id.move_ids:
                    if move.state in ('done', 'assigned'):
                        moves_done.append(move)
                    else:
                        moves_other.append(move)
            qty_uom_all = line.product_uom_qty
            qty_uos_all = line.product_uos_qty
            if all([x.product_uom.id == line.product_uom.id for x in moves_done]):
                qty_uom_done = sum([x.product_qty for x in moves_done])
                qty_uos_done = sum([x.product_uos_qty for x in moves_done])
            else:
                raise osv.except_osv('Could not copy order', 'Product UoMs are different between the stock moves and the order lines.')

            if qty_uom_done == qty_uom_all: # All done, entire line is read-only
                sol_obj.write(cr, uid, line.id,
                            {
                                'original_done': True,
                                'state': 'confirmed',
                            }, context=context)
            elif qty_uom_done > 0:
                sol_obj.write(cr, uid, line.id,
                            {
                                'product_uom_qty': qty_uom_all - qty_uom_done,
                                'product_uos_qty': qty_uos_all - qty_uos_done,
                            }, context=context)
                new_line_id = sol_obj.copy(cr, uid, line.id,
                            default={
                                'original_done': True,
                                'product_uom_qty': qty_uom_done,
                                'product_uos_qty': qty_uos_done,
                            }, context=context)
                sol_obj.write(cr, uid, new_line_id,
                            {
                                'original_line_id': line.original_line_id.id,
                            }, context=context)
            else:
                pass # No action where none are done
        return

    def migrate_moves_to_edit(self, cr, uid, ids, context=None):
        line_obj = self.pool.get('sale.order.line')
        move_obj = self.pool.get('stock.move')
        pick_obj = self.pool.get('stock.picking')
        proc_obj = self.pool.get('procurement.order')
        wf_service = netsvc.LocalService("workflow")

        if not isinstance(ids, (list, tuple)):
            ids = [ids,]
        for order in self.browse(cr, uid, ids, context=context):
            if not order.original_order:
                raise osv.except_osv('Error', 'Attempted to migrate moves for edited order %d but order has no original order' % (order.name,))

            pickings_to_move = []   # Entire pickings being moved to the new order
            moves_to_move = []      # Moves not in the above pickings being moved to the new order's main picking
            pickings_to_cancel = [] # Pickings in the old order which need cancelling after moves are moved
            for picking in order.original_order.picking_ids:
                # Are we moving the entire picking or just individual moves
                if picking.state in ('done'): # assigned pickings can contain confirmed moves so don't move them
                    move_picking = True
                    pickings_to_move.append(picking)
                else:
                    move_picking = False
                for move in picking.move_lines:
                    if move.state in ('done', 'assigned'):
                        if not move_picking:
                            moves_to_move.append(move)

                        proc_ids = proc_obj.search(cr, uid, [('move_id', '=', move.id), ('state', '!=', 'cancel')])
                        if proc_ids:
                            proc_id = proc_ids[0]
                        else:
                            proc_id = False

                        # If linked to a done edit-line it is OK
                        new_line = line_obj.search(cr, uid, [('order_id', '=', order.id), ('original_line_id', '=', move.sale_line_id.id), ('original_done', '=', True)], context=context)
                        if new_line and new_line[0]:
                            line = line_obj.browse(cr, uid, new_line[0], context=context)
                            line_obj.write(cr, uid, [line.id,], {'procurement_id': proc_id})
                            move_obj.write(cr, uid, [move.id,], {'sale_line_id': line.id,}, context=context)
                            continue

                        # If linked to an edit-line, check qty then it is OK
                        new_line = line_obj.search(cr, uid, [('order_id', '=', order.id), ('original_line_id', '=', move.sale_line_id.id), ('product_id', '=', move.sale_line_id.product_id.id), ('original_done', '=', False)], context=context)
                        if new_line and new_line[0]:
                            line = line_obj.browse(cr, uid, new_line[0], context=context)
                            if line.product_uom_qty < move.product_qty:
                                raise osv.except_osv('Could not edit order', 'Moves have been processed since the origional edit and are removed in the new order. Please cancel the edit and re-edit the origional.')
                            line_obj.write(cr, uid, [line.id,], {'procurement_id': proc_id})
                            move_obj.write(cr, uid, [move.id,], {'sale_line_id': line.id,}, context=context)
                            continue

                        # If not linked to an edit-line, find other lines for it
                        new_lines = line_obj.search(cr, uid, [('order_id', '=', order.id), ('original_line_id', '=', False), ('product_id', '=', move.sale_line_id.product_id.id)], context=context)
                        for line in line_obj.browse(cr, uid, new_lines, context=context):
                            if line.product_uom_qty >= move.product_qty:
                                line_obj.write(cr, uid, [line.id,], {'procurement_id': proc_id})
                                move_obj.write(cr, uid, [move.id,], {'sale_line_id': line.id,}, context=context)
                                break
                        else:
                            raise osv.except_osv('Could not edit order', 'Moves have been processed since the origional edit and are removed in the new order. Please cancel the edit and re-edit the origional.')

                if not move_picking:
                    pickings_to_cancel.append(picking)

            if pickings_to_move:
                pick_obj.write(cr, uid, [x.id for x in pickings_to_move], {'sale_id': order.id}, context=context)
            if moves_to_move:
                move_obj.write(cr, uid, [x.id for x in moves_to_move], {'picking_id': order.picking_ids[0].id}, context=context)
            for picking in pickings_to_cancel:
                wf_service.trg_validate(uid, 'stock.picking', picking.id, 'button_cancel', cr)

            order = self.browse(cr, uid, order.id, context=context) # Refresh order
            for line in order.order_line:
                moves_done = []
                moves_other = []
                for move in line.move_ids:
                    if move.state in ('done', 'assigned'):
                        moves_done.append(move)
                    else:
                        moves_other.append(move)
                qty_uom_done = sum([x.product_qty for x in moves_done])
                qty_uom_notdone = sum([x.product_qty for x in moves_other])

                if qty_uom_done > line.product_uom_qty:
                    raise osv.except_osv('Integrity Error', 'The qty of done and available moves exceeds the line qty')

                qty_uom_diff = (qty_uom_done + qty_uom_notdone) - line.product_uom_qty
                if qty_uom_diff > 0:
                    if qty_uom_diff > qty_uom_notdone:
                        raise osv.except_osv('Integrity Error', 'The qty of done and available moves exceeds the line qty')

                    # Reduce/remove new moves which are replaced by done/assigned moved in original order
                    for move in moves_other:
                        if qty_uom_diff == 0:
                            break
                        if qty_uom_diff >= move.product_qty: # This move and it's procurement can be discarded
                            qty_uom_diff -= move.product_qty
                            move_obj.action_cancel(cr, uid, [move.id,], context=context)
                            proc_ids = proc_obj.search(cr, uid, [('move_id', '=', move.id)])
                            if proc_ids: # Detach the now cancelled procurement order from the SO lines
                                proc_obj.action_cancel(cr, uid, proc_ids)
                                line_ids = line_obj.search(cr, uid, [('procurement_id', 'in', proc_ids)])
                                if line_ids:
                                    line_obj.write(cr, uid, line_ids, {'procurement_id': False})
                            move_obj.unlink(cr, uid, [move.id,], context={'call_unlink': True}) # Force a delete of the redundant move
                        elif move.product_qty - qty_uom_diff > 0: # This move can be reduced
                            move_obj.write(cr, uid, [move.id,], {'product_qty': move.product_qty - qty_uom_diff, 'product_uos_qty': move.product_qty - qty_uom_diff})
                            proc_ids = proc_obj.search(cr, uid, [('move_id', '=', move.id)])
                            if proc_ids: # Update the procurements for this move
                                proc_obj.write(cr, uid, proc_ids, {'product_qty': move.product_qty - qty_uom_diff, 'product_uos_qty': move.product_qty - qty_uom_diff})
                            qty_uom_diff = 0
        return

    def migrate_invoices_to_edit(self, cr, uid, ids, context=None):
        if not isinstance(ids, (list, tuple)):
            ids = [ids,]
        for order in self.browse(cr, uid, ids, context=context):
            if not order.original_order:
                raise osv.except_osv('Error', 'Attempted to migrate invoices for edited order %d but order has no original order' % (order.name,))

            invoice_ids = [x.id for x in order.original_order.invoice_ids]
            self.write(cr, uid, [order.original_order.id,], {'invoice_ids': [[6, 0, []]]}, context=context)
            self.write(cr, uid, [order.id,], {'invoice_ids': [[6, 0, invoice_ids]]}, context=context)
        return

    def validate_after_edit(self, cr, uid, ids, context=None):
        if not isinstance(ids, (list, tuple)):
            ids = [ids,]
        for order in self.browse(cr, uid, ids, context=context):
            for line in order.order_line:
                if line.product_id and line.product_id.product_tmpl_id.type in ('product', 'consu') and \
                        line.product_uom_qty != sum([x.product_qty for x in line.move_ids]):
                    raise osv.except_osv('Integrity Error', 'The qty of moves is different to the line qty')
                if line.procurement_id and line.procurement_id.state == 'cancel':
                    raise osv.except_osv('Integrity Error', 'A cancelled procurement is linked to the edited order')
            for picking in order.picking_ids:
                for move in picking.move_lines:
                    if move.sale_line_id.id not in [x.id for x in order.order_line]:
                        raise osv.except_osv('Integrity Error', 'A move is not linked to a sale order line in this order')
            self.write(cr, uid, [order.original_order.id,], {'edited_order': order.id}, context=context) # Mark the old order so it cannot be reset to draft

    def cancel_after_edit(self, cr, uid, ids, context=None):
        if not isinstance(ids, (list, tuple)):
            ids = [ids,]
        for order in self.browse(cr, uid, ids, context=context):
            for pick in order.picking_ids:
                if pick.state not in ('cancel'):
                    raise osv.except_osv('Integrity Error', 'Original order still has active pickings')
            self.action_cancel(cr, uid, [order.id,], context=context) # The workflow triggers in this function to the correct activity
            order = self.browse(cr, uid, order.id, context=context)
            if order.state != 'cancel':
                raise osv.except_osv('Integrity Error', 'Original order could not be cancelled')

    def action_ship_create(self, cr, uid, ids, context=None):
        if context is None:
            context = {}

        res = super(sale_order, self).action_ship_create(cr, uid, ids, context)

        for order in self.browse(cr, uid, ids, context=context):
            if order.original_order:
                context.update({'validate_edit_confirm': True})
                # Validate the order can still be edited
                self.validate_for_edit(cr, uid, [order.original_order.id,], context=context)
                # Move pickings from old order to new order
                self.migrate_moves_to_edit(cr, uid, [order.id,], context=context)
                # Move invoices from old order to new order
                self.migrate_invoices_to_edit(cr, uid, [order.id,], context=context)
                # Validate integrity of new order
                self.validate_after_edit(cr, uid, [order.id,], context=context)
                # Cancel old order
                self.cancel_after_edit(cr, uid, [order.original_order.id,], context=context)
        return res

sale_order()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
