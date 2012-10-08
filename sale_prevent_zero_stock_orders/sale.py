# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2012 credativ (http://www.credativ.co.uk). All Rights Reserved
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

from osv import fields, osv
from tools.translate import _
from tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, float_compare
import time

class sale_order_line(osv.osv):
    _inherit = 'sale.order.line'

    def product_id_change(self, cr, uid, ids, pricelist, product, qty=0,
            uom=False, qty_uos=0, uos=False, name='', partner_id=False,
            lang=False, update_tax=True, date_order=False, packaging=False, fiscal_position=False, flag=False, context=None):
        
        res = super(sale_order_line, self).product_id_change(cr, uid, ids, pricelist, product, qty=qty,
            uom=uom, qty_uos=qty_uos, uos=uos, name=name, partner_id=partner_id,
            lang=lang, update_tax=update_tax, date_order=date_order, packaging=packaging, fiscal_position=fiscal_position, flag=flag, context=context)
        
        if product:
            product_uom_obj = self.pool.get('product.uom')
            product_obj = self.pool.get('product.product')
            product_obj = product_obj.browse(cr, uid, product, context=context)
            uom2 = False
            if uom:
                uom2 = product_uom_obj.browse(cr, uid, uom)
                if product_obj.uom_id.category_id.id != uom2.category_id.id:
                    uom = False
            if not uom2:
                uom2 = product_obj.uom_id
            compare_qty = float_compare(product_obj.virtual_available * uom2.factor, qty * product_obj.uom_id.factor, precision_rounding=product_obj.uom_id.rounding)
            
            if (product_obj.type=='product') and int(compare_qty) == -1 \
            and (product_obj.procure_method=='make_to_stock'):
                result = {'product_id': False, 'product_packaging': False, 'product_uos_qty': 1, 'th_weight': 0, 'name': '', 'notes': '', 
                          'product_uom_qty': 1, 'delay': 0.0, 'product_uos': False, 'type': u'make_to_stock', 'price_unit': 0.0, 'tax_id':[]
                          }
                
            else:
                result = res['value']
            
            res_new = {'value': result, 'domain': res['domain'], 'warning': res['warning']}
        else:
            res_new = res
        
        return res_new

sale_order_line()

