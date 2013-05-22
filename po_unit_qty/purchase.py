# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution    
#    Copyright (C) 2013 credativ Ltd (<http://credativ.co.uk>).
#    All Rights Reserved
#    $Id$
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
import decimal_precision as dp

class purchase_order_line(osv.osv):
    _inherit = 'purchase.order.line'
    
    def onchange_product_uom(self, cr, uid, ids, pricelist_id, product_id, qty, uom_id,
            partner_id, date_order=False, fiscal_position_id=False, date_planned=False,
            name=False, price_unit=False, notes=False, context=None):
        """
        onchange handler of product_uom.
        """
        if not uom_id:
            return {'value': {'price_unit': price_unit or 0.0, 'name': name or '', 'notes': notes or'', 'product_uom' : uom_id or False}}
        return self.onchange_product_id(cr, uid, ids, pricelist_id, product_id, qty, uom_id,
            partner_id, date_order=date_order, fiscal_position_id=fiscal_position_id, date_planned=date_planned,
            name=name, price_unit=price_unit, notes=notes, context=context)
    
    def onchange_product_id(self, cr, uid, ids, pricelist_id, product_id, qty, uom_id,
            partner_id, date_order=False, fiscal_position_id=False, date_planned=False,
            name=False, price_unit=False, notes=False, context=None):
        """
        onchange handler of product_id.
        """
        res = super(purchase_order_line, self).onchange_product_id(cr,uid,ids,pricelist_id, product_id, qty, uom_id,
            partner_id, date_order=date_order, fiscal_position_id=fiscal_position_id, date_planned=date_planned,
            name=name, price_unit=price_unit, notes=notes, context=context)
        if product_id and uom_id:
            uom = self.pool.get('product.uom').browse(cr,uid,uom_id,context=context)
            qty_per_uom = 1.0 / uom.factor
            value={
                'qty_per_uom': qty_per_uom,
                'unit_qty': qty * qty_per_uom
                   }
            res['value'].update(value)
            res.setdefault('domain', {}).setdefault('product_uom', []).extend(['|', ('product_ids','in', [product_id]), ('product_ids', '!=', [])])
        return res

    def onchange_unit_qty(self, cr, uid, ids, pricelist_id, product_id, qty, uom_id,
            partner_id, date_order=False, fiscal_position_id=False, date_planned=False,
            name=False, price_unit=False, notes=False, unit_qty=0.0, qty_per_uom=0.0, context=None):
        """
        onchange handler of unit_qty.
        """
        res = {}
        if product_id and uom_id:
            value={
                'product_qty': float(unit_qty) / qty_per_uom,
                   }
            res['value'] = value
        return res

    def _get_qty_per_uom(self, cr, uid, ids, name, data, context=None):
        res = {}
        for pol in self.browse(cr, uid, ids, context):
            uom = pol.product_uom
            if uom:
                res[pol.id] = 1.0 / uom.factor
            else:
                res[pol.id] = 1.0
        return res
        
    def _get_unit_qty(self, cr, uid, ids, name, data, context=None):
        res = {}
        for pol in self.browse(cr, uid, ids, context):
            res[pol.id] = pol.product_qty * pol.qty_per_uom
        return res
        
        
    _columns = {
                'qty_per_uom': fields.function(_get_qty_per_uom, type='float', string='Quantity per UOM', digits_compute=dp.get_precision('Product UoM'), required=True, readonly=True),
                'unit_qty': fields.function(_get_unit_qty, type='float', string='Unit Quantity', digits_compute=dp.get_precision('Product UoM'), required=True),
    }
    
purchase_order_line()
