# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution    
#    Copyright (C) 2013 credativ ltd (<http://www.credativ.co.uk>). All Rights Reserved
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

class purchase_order(osv.osv):
    _inherit = 'purchase.order'
    
    def onchange_po_lines(self, cr, uid, ids, order_lines, context=None):
        import ipdb; ipdb.set_trace()
        return {}
    
purchase_order()

class purchase_order_line(osv.osv):
    _inherit = 'purchase.order.line'
    
    def _get_product_qty(self, cr, uid, ids, field_names=None, args=False, context=None):
        """Required in order to show 0.0 instead of an empty string when using a related field"""
        product_obj = self.pool.get('product.product')
        res = {}
        
        if not field_names:
            return res
        
        for id in ids:
            res[id] = dict(zip(field_names, [0.0,]*len(field_names)))
        
        for pol in self.browse(cr, uid, ids, context=context):
            for field_name in field_names:
                if field_name[-6:] == '_dummy':
                    field_name_read = field_name[:-6]
                else:
                    field_name_read = field_name
                if pol.product_id and hasattr(pol.product_id, field_name_read):
                    res[id][field_name] = getattr(pol.product_id, field_name_read) or 0.0
                else:
                    res[id][field_name] = 0.0
        
        return res
    
    def onchange_product_id(self, cr, uid, ids, pricelist_id, product_id, qty, uom_id,
            partner_id, date_order=False, fiscal_position_id=False, date_planned=False,
            name=False, price_unit=False, notes=False, context=None):
        '''Product onchange overridden to pass values of stock on hand and Incoming Stock'''
        product_obj = self.pool.get('product.product')
        
        qty_dic={'incoming_qty': 0.0, 'qty_available': 0.0}
        if product_id:
            stock = product_obj.read(cr, uid, product_id, ['incoming_qty', 'qty_available'], context=context)
            qty_dic['incoming_qty'] = stock.get('incoming_qty', 0.0)
            qty_dic['qty_available'] = stock.get('qty_available', 0.0)
            qty_dic['incoming_qty_dummy'] = stock.get('incoming_qty', 0.0)
            qty_dic['qty_available_dummy'] = stock.get('qty_available', 0.0)
            
        res_values =  super(purchase_order_line,self).onchange_product_id(cr, uid, ids, pricelist_id, product_id, qty, uom_id,
            partner_id, date_order=date_order, fiscal_position_id=fiscal_position_id, date_planned=date_planned,
            name=name, price_unit=price_unit, notes=notes, context=context)
        
        res_values.setdefault('value', {}).update(qty_dic)
        
        return res_values
    
    product_id_change = onchange_product_id
    
    # _dummy fields are required as a work around where readonly fields are not copied from the form to the tree for
    # PO lines. We have to mirror the fields so one is readonly and the other is editable and invisible
    _columns = {
        'incoming_qty': fields.function(_get_product_qty, method=True, type='float', string='Incoming Stock', digits_compute=dp.get_precision('Product UoM'), help='Incoming Product Stock', multi='_get_product_qty',),
        'qty_available': fields.function(_get_product_qty, method=True, type='float', string='On Hand Stock', digits_compute=dp.get_precision('Product UoM'), help='Product Stock on hand', multi='_get_product_qty',),
        'incoming_qty_dummy': fields.function(_get_product_qty, method=True, type='float', string='Incoming Stock', digits_compute=dp.get_precision('Product UoM'), help='Incoming Product Stock', multi='_get_product_qty',),
        'qty_available_dummy': fields.function(_get_product_qty, method=True, type='float', string='On Hand Stock', digits_compute=dp.get_precision('Product UoM'), help='Product Stock on hand', multi='_get_product_qty',),
        }
    
purchase_order_line()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
