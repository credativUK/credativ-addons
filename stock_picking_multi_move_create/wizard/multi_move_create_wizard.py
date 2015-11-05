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

import openerp.addons.decimal_precision as dp

class MultiMoveCreateWizard(osv.osv_memory):
    _name = "stock.picking.multi.move.create.wizard"
    _description = "Create multiple moves"
    _columns = {
        'picking_id' : fields.many2one('stock.picking', 'Picking', required=True),
        'product_ids' : fields.many2many('product.product', 'multi_move_create_product_rel', 'product_id', 'multi_move_create_id', 'Products', domain=[('type', '=', 'product')]),
        'draft_moves' : fields.one2many('stock.picking.multi.move.create.wizard.lines', 'wizard_id', 'Draft Moves'),
        'location_id': fields.many2one('stock.location', 'Source Location', required=True),
        'location_dest_id': fields.many2one('stock.location', 'Destination Location', required=True),
        }

    def default_get(self, cr, uid, fields, context):
        picking_id = context and context.get('active_id', False) or False
        res = super(MultiMoveCreateWizard, self).default_get(cr, uid, fields, context=context)
        picking = self.pool.get('stock.picking').browse(cr, uid, picking_id, context=context)
        if picking and picking.move_lines:
            # Set default locations based on one of the existing moves
            location_id = picking.move_lines[0].location_id.id
            location_dest_id = picking.move_lines[0].location_dest_id.id
            res.update({'location_id': location_id, 'location_dest_id': location_dest_id})
        res.update({'picking_id': picking_id or False})
        return res

    def action_update(self, cr, uid, ids, context=None):
        # Synchronise product_ids to the products in draft_moves
        wizard_line_obj = self.pool.get('stock.picking.multi.move.create.wizard.lines')
        for wizard_data in self.read(cr, uid, ids, ['product_ids', 'draft_moves'], context=context):
            draft_moves_datas = wizard_line_obj.read(cr, uid, wizard_data['draft_moves'], ['product_id'], context=context)
            draft_moves_to_remove = []
            products_with_moves = []
            for draft_moves_data in draft_moves_datas:
                if draft_moves_data['product_id'][0] in products_with_moves:
                    # Skip product_id as already appended to products_with_moves
                    continue
                if draft_moves_data['product_id'][0] in wizard_data['product_ids']:
                    # Build list of product ids which already have at least one draft move
                    products_with_moves.append(draft_moves_data['product_id'][0])
                else:
                    # This product has been removed, so the draft move should also be removed
                    draft_moves_to_remove.append(draft_moves_data['id'])
            moves_to_create = [product_id for product_id in wizard_data['product_ids'] if product_id not in products_with_moves]
            wizard_line_obj.unlink(cr, uid, draft_moves_to_remove, context=context)
            for product_id in moves_to_create:
                create_vals = {'wizard_id': wizard_data['id'], 'product_id': product_id, 'product_qty': 1}
                wizard_line_obj.create(cr, uid, create_vals, context=context)
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'stock.picking.multi.move.create.wizard',
            'view_type': 'form',
            'view_mode': 'form',
            'res_id': wizard_data['id'],
            'target':'new',
            'nodestroy': True,
            'context': context,
            }

    def action_confirm(self, cr, uid, ids, context=None):
        # Add moves to picking based on selected products, quantities and locations
        wizard_line_obj = self.pool.get('stock.picking.multi.move.create.wizard.lines')
        move_obj = self.pool.get('stock.move')
        prod_obj = self.pool.get('product.product')
        pick_obj = self.pool.get('stock.picking')
        for wizard_data in self.read(cr, uid, ids, ['picking_id', 'draft_moves', 'location_id', 'location_dest_id'], context=context): # also read 
            picking_id = wizard_data['picking_id'][0]
            location_id = wizard_data['location_id'][0]
            location_dest_id = wizard_data['location_dest_id'][0]
            picking = pick_obj.browse(cr, uid, picking_id, context=context)
            existing_move_ids = pick_obj.read(cr, uid, picking_id, ['move_lines'], context=context)['move_lines']
            # Update existing moves to have the same locations
            move_obj.write(cr, uid, existing_move_ids, {'location_id': location_id, 'location_dest_id': location_dest_id}, context=context)
            for wizard_line in wizard_line_obj.read(cr,uid, wizard_data['draft_moves'], ['product_id', 'product_qty'], context=context):
                if wizard_line['product_qty'] > 0:
                    product = prod_obj.browse(cr, uid, wizard_line['product_id'][0], context=context)
                    vals = {
                        'name': product.name,
                        'picking_id': picking_id,
                        'product_id': product.id,
                        'product_qty': wizard_line['product_qty'],
                        'product_uom': product.uom_id.id,
                        'location_id': location_id,
                        'location_dest_id': location_dest_id,
                        'state': 'draft',
                    }
                    move_obj.create(cr, uid, vals, context=context)
        return True

class MultiMoveCreateWizardLines(osv.osv_memory):
    _name = "stock.picking.multi.move.create.wizard.lines"
    _description = "Draft moves"
    _columns = {
        'wizard_id': fields.many2one('stock.picking.multi.move.create.wizard', 'Move creation wizard', required=True, ondelete='cascade', readonly=True),
        'product_id' : fields.many2one('product.product', 'Product', required=True),
        'product_qty' : fields.float('Quantity', digits_compute=dp.get_precision('Product Unit of Measure'), required=True),
            }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
