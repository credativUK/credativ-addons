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

from openerp.osv import osv, fields
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp

class ProductProduct(osv.osv):
    _inherit = "product.product"

    def _product_available_supplier(self, cr, uid, ids, field_names=None, arg=False, context=None):
        if context is None:
            context = {}
        res = {id: {} for id in ids}

        location_obj = self.pool.get('stock.location')
        warehouse_obj = self.pool.get('stock.warehouse')
        shop_obj = self.pool.get('sale.shop')

        c = context.copy()
        c.update({ 'states': ('confirmed','waiting','assigned','done'), 'what': ('in', 'out') })

        if c.get('shop', False):
            warehouse_id = shop_obj.read(cr, uid, int(c['shop']), ['warehouse_id'])['warehouse_id'][0]
            if warehouse_id:
                del c['shop']
                c['warehouse'] = warehouse_id

        if c.get('location', False):
            if type(c['location']) == type(1):
                location_ids = [c['location']]
            elif type(c['location']) in (type(''), type(u'')):
                location_ids = location_obj.search(cr, uid, [('name','ilike',c['location'])], context=c)
            else:
                location_ids = c['location']
            warehouse_id = warehouse_obj.search(cr, uid, [('lot_stock_id', 'in', location_ids)], context=c)
            if warehouse_id:
                c['warehouse'] = warehouse_id[0]

        if not c.get('warehouse', False):
            warehouse_ids = warehouse_obj.search(cr, uid, [])
            lot_ids = warehouse_obj.read(cr, uid, warehouse_ids, ['lot_supplier_virtual_id'])
            location_ids = []
            for lot_id in lot_ids:
                if lot_id['lot_supplier_virtual_id']:
                    location_ids.append(lot_id['lot_supplier_virtual_id'][0])
            if location_ids:
                 c['location'] = location_ids
        elif c.get('warehouse', False):
            lot_id = warehouse_obj.read(cr, uid, int(c['warehouse']), ['lot_supplier_virtual_id'])['lot_supplier_virtual_id'][0]
            if lot_id:
                del c['warehouse']
                c['location'] = lot_id

        stock = {}
        if c.get('location', False):
            stock = self.get_product_available(cr, uid, ids, context=c)
        for id in ids:
            res[id]['supplier_virtual_available'] = stock.get(id, 0.0)

        if 'supplier_virtual_available_combined' in field_names:
            va_stock_data = self.read(cr, uid, ids, ['virtual_available'])
            va_stock = {v['id']: v['virtual_available'] for v in va_stock_data}
            for id in ids:
                res[id]['supplier_virtual_available_combined'] = va_stock.get(id, 0.0) + stock.get(id, 0.0)

        return res

    _columns = {
        'supplier_virtual_available': fields.function(_product_available_supplier, multi='supplier_virtual_available',
            type='float',  digits_compute=dp.get_precision('Product Unit of Measure'),
            string='Supplier Available Quantity',
            help="Forecast quantity (computed as Quantity On Hand "
                 "- Outgoing + Incoming) at the virtual supplier location "
                 "for the current warehouse if applicable, otherwise 0."),
        'supplier_virtual_available_combined': fields.function(_product_available_supplier, multi='supplier_virtual_available',
            type='float',  digits_compute=dp.get_precision('Product Unit of Measure'),
            string='Available Quantity inc. Supplier',
            help="Forecast quantity (computed as Quantity On Hand "
                 "- Outgoing + Incoming) at the virtual supplier location "
                 "for the current warehouse if applicable, otherwise 0, plus "
                 "the normal forecast quantity."),
    }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: