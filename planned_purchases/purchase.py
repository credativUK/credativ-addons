# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2009 credativ Ltd (<http://credativ.co.uk>).
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

import time
from datetime import datetime
from dateutil.relativedelta import relativedelta
from osv import osv

class procurement_order(osv.osv):
    _inherit = 'procurement.order'    

    def make_po(self, cr, uid, ids, context=None):
        """ Make purchase order from procurement
        @return: New created Purchase Orders procurement wise
        """
        res = {}
        if context is None:
            context = {}
        company = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id
        partner_obj = self.pool.get('res.partner')
        uom_obj = self.pool.get('product.uom')
        pricelist_obj = self.pool.get('product.pricelist')
        prod_obj = self.pool.get('product.product')
        acc_pos_obj = self.pool.get('account.fiscal.position')
        po_obj = self.pool.get('purchase.order')
        po_line_obj = self.pool.get('purchase.order.line')
        for procurement in self.browse(cr, uid, ids, context=context):
            res_id = procurement.move_id and procurement.move_id.id or False
            partner = procurement.product_id.seller_id # Taken Main Supplier of Product of Procurement.
            seller_qty = procurement.product_id.seller_qty
            seller_delay = int(procurement.product_id.seller_delay)
            partner_id = partner.id
            address_id = partner_obj.address_get(cr, uid, [partner_id], ['delivery'])['delivery']
            pricelist_id = partner.property_product_pricelist_purchase.id
            fiscal_position = partner.property_account_position and partner.property_account_position.id or False

            uom_id = procurement.product_id.uom_po_id.id
            
            qty = uom_obj._compute_qty(cr, uid, procurement.product_uom.id, procurement.product_qty, uom_id)
            if seller_qty:
                qty = max(qty,seller_qty)

            price = pricelist_obj.price_get(cr, uid, [pricelist_id], procurement.product_id.id, qty, partner_id, {'uom': uom_id})[pricelist_id]

            newdate = datetime.strptime(procurement.date_planned, '%Y-%m-%d %H:%M:%S')
            newdate = (newdate - relativedelta(days=company.po_lead)) - relativedelta(days=seller_delay)

            res_onchange = po_line_obj.product_id_change(cr, uid, ids, pricelist_id, procurement.product_id.id, qty, uom_id,
                partner_id, time.strftime('%Y-%m-%d'), fiscal_position=fiscal_position, date_planned=datetime.now() + relativedelta(days=seller_delay or 0.0),
            name=procurement.name, price_unit=procurement.product_id.list_price, notes=procurement.product_id.description_purchase)

            #Passing partner_id to context for purchase order line integrity of Line name
            context.update({'lang': partner.lang, 'partner_id': partner_id})

            product = prod_obj.browse(cr, uid, procurement.product_id.id, context=context)

            line = {
                'name': product.partner_ref,
                'product_qty': res_onchange['value']['product_qty'],
                'product_id': procurement.product_id.id,
                'product_uom': res_onchange['value']['product_uom'],
                'price_unit': res_onchange['value']['price_unit'],
                'date_planned': newdate.strftime('%Y-%m-%d %H:%M:%S'),
                'move_dest_id': res_id,
                'notes': product.description_purchase,
            }

            taxes_ids = procurement.product_id.product_tmpl_id.supplier_taxes_id
            taxes = acc_pos_obj.map_tax(cr, uid, partner.property_account_position, taxes_ids)
            line.update({
                'taxes_id': [(6,0,taxes)]
            })

            #Update an existing purchase order
            user_class = self.pool.get('res.users')
            user_company_id = user_class.browse(cr, uid, uid, context = context).company_id.id
            po_exists = po_obj.search(cr, uid, [('company_id','=', user_company_id),
            ('partner_id', '=', partner_id),
            ('state', 'in', ['draft','planned'])])

            if po_exists:
                purchase_id = po_exists[0]

            else:
                purchase_id = po_obj.create(cr, uid, {
                'state': 'planned',
                'origin': procurement.origin,
                'partner_id': partner_id,
                'partner_address_id': address_id,
                'pricelist_id': pricelist_id,
                'location_id': procurement.location_id.id,
                'company_id': procurement.company_id.id,
                'fiscal_position': partner.property_account_position and partner.property_account_position.id or False
                })

            line_exists = po_line_obj.search(cr, uid, [('product_id','=',procurement.product_id.id),('order_id','=',purchase_id)])
            if line_exists:
                purchase_line_id = line_exists[0]
                quantity = po_line_obj.browse(cr, uid, purchase_line_id).product_qty + res_onchange['value']['product_qty']
                po_line_obj.write(cr, uid, [purchase_line_id], {'product_qty': quantity})
            else:
                line.update({'order_id': purchase_id})
                purchase_line_id = po_line_obj.create(cr, uid, line)
            res[procurement.id] = purchase_id
            self.write(cr, uid, [procurement.id], {'state': 'running', 'purchase_id': purchase_id, 'purchase_line_id':purchase_line_id})
            return res

procurement_order()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
