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

class purchase_order_line(osv.osv):
    _inherit = 'purchase.order.line'
    
    def _compute_cbm(self,cr,uid,ids,field_name,args,context=None):
        if context is None:
            context={}
        res={}
        for po_line in self.browse(cr,uid,ids,context=context):
            cbm = 0
            for package in po_line.product_id.packaging:
                cbm += (package.length * package.width * package.height * 10**-6)
            res[po_line.id] = {
                'cbm':cbm,
                'cbm_total':cbm*po_line.product_qty     
                   }
        return res
    
    def onchange_product_id(self, cr, uid, ids, pricelist_id, product_id, qty, uom_id,
            partner_id, date_order=False, fiscal_position_id=False, date_planned=False,
            name=False, price_unit=False, notes=False, context=None):
        """
        onchange handler of product_id.
        """
        res = super(purchase_order_line, self).onchange_product_id(cr,uid,ids,pricelist_id, product_id, qty, uom_id,
            partner_id, date_order=date_order, fiscal_position_id=fiscal_position_id, date_planned=date_planned,
            name=name, price_unit=price_unit, notes=notes, context=context)
        
        if product_id:
            product = self.pool.get('product.product').browse(cr,uid,product_id,context=context)
            cbm = 0
            for package in product.packaging:
                #Converts to CM multiplying 10***-6
                cbm += (package.length * package.width * package.height * 10**-6)
            value={
                'cbm':cbm,
                'cbm_total':cbm*res['value']['product_qty']
                   }
            res['value'].update(value)
        return res


    _columns = {
        'cbm': fields.function(_compute_cbm, method=True, string='CBM', help='Cubic meters (CBM)',
                store=False,multi='cal_cbm'),
        'cbm_total': fields.function(_compute_cbm, method=True, string='Subtotal CBM', help='Total Cubic meters (CBM)',
                store=False,multi='cal_cbm'),
    }

purchase_order_line()
