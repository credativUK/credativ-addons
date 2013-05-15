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

from osv import osv,fields
from collections import defaultdict
import decimal_precision as dp

class purchase_order_line(osv.osv):
    _inherit = 'purchase.order.line'
    
    def _get_product_available(self,cr,uid,ids,context=None):
        '''Method to get product stock '''
                
        return self.pool.get('product.product').\
                    get_product_available(cr, uid, ids, context=context)
    
    def _product_available(self, cr, uid, ids, field_names=None, arg=False, context=None):
        """ Finds the incoming and outgoing quantity of product.
        @return: Dictionary of values
        """

        stock_mapping = {'qty_available':'out','incoming_qty':'in'}
        
        if not field_names:
            field_names = False
        if context is None:
            context = {} 
        res = {}
        
        for id in ids:
            if field_names not in stock_mapping.keys():
                continue
            c = context.copy()
            if field_names == 'qty_available':
                c.update({ 'states': ('done',), 'what': ('in', 'out') })
            else:
                c.update({ 'states': ('confirmed','waiting','assigned'), 'what': ('in',) })
            product_id = self.browse(cr,uid,id,context=context).product_id.id
            stock = self._get_product_available(cr, uid, [product_id], context=c)
            res[id] = stock.get(product_id,0.0)
        
        return res
    
    def onchange_product_id(self, cr, uid, ids, pricelist_id, product_id, qty, uom_id,
            partner_id, date_order=False, fiscal_position_id=False, date_planned=False,
            name=False, price_unit=False, notes=False, context=None):
        '''Product onchange overridden to pass values of stock on hand and Incoming Stock'''
        
        qty_dic = {'qty_available':0.0,'incoming_qty':0.0}
        mapping_dic = {'qty_available':{ 'states': ('done',), 'what': ('in', 'out') },\
                       'incoming_qty':{ 'states': ('confirmed','waiting','assigned'), 'what': ('in',) }}
        
        if context is None:
            context = {}
        
        if product_id:
            for avail_type in mapping_dic.keys():
                c = context.copy()
                c.update(mapping_dic[avail_type])
                stock = self._get_product_available(cr, uid, [product_id], context=c)
                qty_dic[avail_type] = stock.get(product_id,0.0)
            
        res_values =  super(purchase_order_line,self).onchange_product_id(cr, uid, ids, pricelist_id, product_id, qty, uom_id,
            partner_id, date_order=date_order, fiscal_position_id=fiscal_position_id, date_planned=date_planned,
            name=name, price_unit=price_unit, notes=notes, context=context)
        
        res_values['value'].update(qty_dic)
        
        return res_values
    
    
    _columns = {
        'incoming_qty': fields.function(_product_available, type='float', string='Incoming Stock',digits_compute=dp.get_precision('Product UoM'),help='Incoming Product Stock'),
        'qty_available': fields.function(_product_available, type='float', string='On Hand Stock',digits_compute=dp.get_precision('Product UoM'),help='Product Stock on hand'),
                }
    
purchase_order_line()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
