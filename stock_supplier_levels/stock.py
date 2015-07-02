# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright 2015 credativ Ltd
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

import time
from openerp.osv import osv, fields
from openerp.tools.translate import _
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT

class StockMove(osv.osv):
    _inherit = "stock.move"

    def reduce_supplier_stock(self, cr, uid, reduce_data, context=None):
        if context is None:
            context = {}

        lot_obj = self.pool.get('stock.production.lot')
        location_obj = self.pool.get('stock.location')
        warehouse_obj = self.pool.get('stock.warehouse')

        move_ids = []

        for (product_id, uom_id, warehouse_id, partner_id), (qty, date, comment) in reduce_data.iteritems():
            warehouse = warehouse_obj.browse(cr, uid, warehouse_id, context=context)
            location_id = warehouse.lot_supplier_virtual_id.id
            location_dest_id = self._default_location_source(cr, uid, {'picking_type': 'in'})

            if not location_id:
                raise osv.except_osv(_('Warning!'), _('There is no supplier stock location configured on the warehouse to reduce supplier stock levels from.'))

            if not location_dest_id:
                raise osv.except_osv(_('Warning!'), _('The default supplier location is not configured, please set one.'))

            # For all lots for this supplier ID and this product, and for no lot, try to reduce by qty
            lot_ids = lot_obj.search(cr, uid, [('product_id', '=', product_id), ('partner_id', '=', partner_id)], context=context)
            for lot_id in lot_ids + [False,]:
                if qty <= 0:
                    break
                # Get supplier stock
                product_context = context.copy()
                product_context.update(uom=uom_id, prodlot_id=lot_id)
                amount = location_obj._product_get(cr, uid, location_id, [product_id], product_context)[product_id]
                # Reduce amount by qty as far as 0, do not go negative
                if amount > 0:
                    reduce_qty = min(amount, qty)
                    qty -= reduce_qty
                    move_id = self.create(cr, uid, {
                                'name': _('Supplier Reduce:') + (comment or ''),
                                'product_id': product_id,
                                'product_uom': uom_id,
                                'prodlot_id': lot_id,
                                'date': date,
                                'product_qty': reduce_qty,
                                'location_id': location_id,
                                'location_dest_id': location_dest_id,
                            }, context=context)
                    move_ids.append(move_id)
            if qty > 0:
                pass # Ignore any stock left over - we don't really care about it but we do not want to go below 0

        if move_ids:
            self.write(cr, uid, move_ids,
                       {'state': 'done',
                       'date': time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)},
                       context=context)

        return True

class StockWarehouse(osv.osv):
    _inherit = "stock.warehouse"

    _columns = {
        'lot_supplier_virtual_id': fields.many2one('stock.location', 'Virtual Supplier Location', domain=[('usage','=','supplier')],
                                                   help="Set this field to a supplier location which keeps track of actual supplier stock. This will not be used for actual ordering of stock."),
        }

class StockLocation(osv.osv):
    _inherit = "stock.location"

    _columns = {
        'supplier_warehouse_ids': fields.one2many('stock.warehouse', 'lot_supplier_virtual_id', 'Warehouses Supplied', readonly=True),
        }

class StockInventory(osv.osv):
    _inherit = "stock.inventory"

    def _inventory_line_hook(self, cr, uid, inventory_line, move_vals):

        stock_obj = self.pool.get('stock.move')
        location_obj = self.pool.get('stock.location')
        warehouse_obj = self.pool.get('stock.warehouse')

        # If we are performing a supplier inventory we need to take/put stock to main supplier location rather than inventory loss
        if location_obj.search(cr, uid, [('id', '=', move_vals.get('location_id', False)), ('usage', '=', 'supplier')]) and \
                warehouse_obj.search(cr, uid, [('lot_supplier_virtual_id', '=', move_vals.get('location_id', False))]):
            source_id = stock_obj._default_location_source(cr, uid, {'picking_type': 'in'})
            if source_id:
                move_vals['location_dest_id'] = source_id
        elif location_obj.search(cr, uid, [('id', '=', move_vals.get('location_dest_id', False)), ('usage', '=', 'supplier')]) and \
                warehouse_obj.search(cr, uid, [('lot_supplier_virtual_id', '=', move_vals.get('location_dest_id', False))]):
            source_id = stock_obj._default_location_source(cr, uid, {'picking_type': 'in'})
            if source_id:
                move_vals['location_id'] = source_id

        if move_vals.get('location_id', False) == move_vals.get('location_dest_id', False):
            raise osv.except_osv(_('Warning!'), _('It is not possible to use the default supplier location for supplier inventories'))

        return super(StockInventory, self)._inventory_line_hook(cr, uid, inventory_line, move_vals)

class StockInventoryLine(osv.osv):
    _inherit = "stock.inventory.line"

    _columns = {
        'prod_lot_id': fields.many2one('stock.production.lot', 'Serial Number', domain="[('product_id','=',product_id)]", help='Serial Number, or supplier name if tracking supplier stock levels'),
    }

class StockProductionLot(osv.osv):
    _inherit = "stock.production.lot"

    _columns = {
        'partner_id': fields.many2one('res.partner', 'Supplier', help='When this lot is used to seperate supplier stock levels, this is the supplier which it relates to'),
    }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: