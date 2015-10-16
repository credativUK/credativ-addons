# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2014 credativ Ltd (<http://credativ.co.uk>).
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
import decimal_precision as dp

def rounding(f, r):
    if not r:
        return f
    return round(f / r) * r

class sale_order_line(osv.osv):
    _inherit = 'sale.order.line'

    def product_uom_change(self, cr, uid, ids, pricelist, product, qty=0, uom=False, qty_uos=0, uos=False, name='', partner_id=False, lang=False, update_tax=True, date_order=False, context=None):
        """
        onchange handler of product_uom.
        """
        if not uom:
            return {'value': {'name': name or '', 'product_uom' : uom or False}}
        return self.product_id_change(cr, uid, ids, pricelist, product, qty, uom, qty_uos, uos, name, partner_id, lang, update_tax, date_order, context=context)

    def product_id_change(self, cr, uid, ids, pricelist, product, qty=0, uom=False, qty_uos=0, uos=False, name='', partner_id=False, lang=False, update_tax=True, date_order=False, packaging=False, fiscal_position=False, flag=False, context=None):
        """
        onchange handler of product_id.
        """
        res = super(sale_order_line, self).product_id_change(cr,uid,ids,pricelist, product, qty, uom, qty_uos, uos, name, partner_id, lang, update_tax, date_order, packaging, fiscal_position, flag, context)

        # Remove warning message restricting a supplier to a single UoM
        if res.get('warning', False) and res['warning'].get('message', False) and res['warning']['message'][0:48] == 'The selected supplier only sells this product by':
            del res['warning']

        if product and uom:
            uom_browse = self.pool.get('product.uom').browse(cr,uid,uom,context=context)
            qty_per_uom = 1.0 / uom_browse.factor
            value={
                'qty_per_uom': qty_per_uom,
                'unit_qty': qty * qty_per_uom
                   }
            res['value'].update(value)
            res.setdefault('domain', {}).setdefault('product_uom', []).extend(['|', ('product_ids','in', [product]), ('product_ids', '!=', [])])
        return res

    def onchange_unit_qty(self, cr, uid, ids, pricelist_id, product_id, qty, uom_id,
            partner_id, date_order=False, fiscal_position_id=False,
            name=False, price_unit=False, unit_qty=0.0, qty_per_uom=0.0, context=None):
        """
        onchange handler of unit_qty.
        """
        res = {}
        if product_id and uom_id:
            uom = self.pool.get('product.uom').browse(cr, uid, uom_id, context=context)
            product_qty = rounding(qty_per_uom and (float(unit_qty) / qty_per_uom) or 0.0, uom.rounding)
            value = {'product_qty': product_qty, 'unit_qty': product_qty * qty_per_uom}
            res['value'] = value
        return res

    def _get_qty_per_uom(self, cr, uid, ids, name, data, context=None):
        res = {}
        for sol in self.browse(cr, uid, ids, context):
            uom = sol.product_uom
            if uom:
                res[sol.id] = 1.0 / uom.factor
            else:
                res[sol.id] = 1.0
        return res

    def _get_unit_qty(self, cr, uid, ids, name, data, context=None):
        res = {}
        for sol in self.browse(cr, uid, ids, context):
            res[sol.id] = sol.product_uom_qty * pol.qty_per_uom
        return res


    _columns = {
                'qty_per_uom': fields.function(_get_qty_per_uom, type='float', string='Quantity per UOM', digits_compute=dp.get_precision('Product UoM'), required=True, readonly=True),
                'unit_qty': fields.function(_get_unit_qty, type='float', string='Unit Quantity', digits_compute=dp.get_precision('Product UoM'), required=True),
    }

    def _search_replace_uom(self,cr,uid,val,context=None):
        '''Search and replace base reference of product uom and product '''

        if 'product_uom' in val:
            product_uom = self.pool.get('product.uom')
            cat_id = product_uom.browse(cr,uid,val['product_uom'],context=context).category_id.id
            #Search uom base reference.
            val['product_uom'] = product_uom.search(cr,uid,[('category_id','=', cat_id), ('factor', '=', 1), ('uom_type','=','reference')],context=context)[0]
            if 'unit_qty' in val:
                uom_qty = val['unit_qty'] / val['product_uom_qty']
                val['product_uom_qty'] = val['unit_qty']
                val['price_unit'] = val['price_unit'] / uom_qty

        return True

    def create(self,cr,uid,vals,context=None):
        ''' Purchase order line create method overide to set product uom '''

        if not context:
            context={}

        self._search_replace_uom(cr, uid, vals, context=context)
        return super(sale_order_line,self).create(cr,uid,vals,context=context)

    def write(self, cr, uid, ids, vals, context=None):
        ''' Purchase order line write method overide to set product uom '''

        if not context:
            context = {}

        self._search_replace_uom(cr, uid, vals, context=context)
        return super(sale_order_line,self).write(cr, uid, ids, vals, context)

sale_order_line()
