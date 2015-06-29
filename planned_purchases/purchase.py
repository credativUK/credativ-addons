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

import time
from datetime import datetime
from dateutil.relativedelta import relativedelta
from osv import osv
from openerp.tools.translate import _
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP

class purchase_order(osv.osv):
    _inherit='purchase.order'

    def merge_po(self,cr,uid,ids=[],context=None):
        '''Auto merge Purchase orders with same supplier and in draft state '''

        if context is None:
            context={}
        po_group_obj = self.pool.get('purchase.order.group')

        #Search for po which are in draft state
        if not ids:
            cr.execute("select id from purchase_order where state='draft' and id in (select purchase_id as id from procurement_order where state='running')")
            ids = map(lambda x: x[0], cr.fetchall())

        #assign ids to active_ids in context
        context['active_ids'] = ids

        #Call merge_orders method from purchase.order.group object to merge PO
        return po_group_obj.merge_orders(cr,uid,[],context=context)

purchase_order()

class procurement_order(osv.osv):
    _inherit = 'procurement.order'

    def _planned_purchases_get_purchases(self, cr, uid, procurement, po_ids, context=None):
        purchase_obj = self.pool.get('purchase.order')
        company_id = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id
        partner_id = procurement.product_id.seller_id.id
        purchase_ids = purchase_obj.search(cr, uid, [('company_id','=', company_id.id),
                                                ('partner_id', '=', partner_id),
                                                ('state', 'in', ['draft']),
                                                ('id', 'in', po_ids),
                                                ('warehouse_id', '=', self._get_warehouse(procurement, company_id)),
                                                ], context=context)
        return purchase_ids

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
        seq_obj = self.pool.get('ir.sequence')
        po_obj = self.pool.get('purchase.order')
        po_line_obj = self.pool.get('purchase.order.line')

        # Merge All PO's which were genereated through scheduler
        cr.execute("select id from purchase_order where state='draft' and id in (select purchase_id as id from procurement_order where state='running')")
        po_ids = map(lambda x: x[0], cr.fetchall())
        #po_obj.merge_po(cr,uid,po_ids,context=context)

        for procurement in self.browse(cr, uid, ids, context=context):
            res_id = procurement.move_id.id
            partner = procurement.product_id.seller_id # Taken Main Supplier of Product of Procurement.
            seller_qty = procurement.product_id.seller_qty
            partner_id = partner.id
            address_id = partner_obj.address_get(cr, uid, [partner_id], ['delivery'])['delivery']
            pricelist_id = partner.property_product_pricelist_purchase.id

            uom_id = procurement.product_id.uom_po_id.id

            qty = uom_obj._compute_qty(cr, uid, procurement.product_uom.id, procurement.product_qty, uom_id)
            if seller_qty:
                qty = max(qty,seller_qty)

            price = pricelist_obj.price_get(cr, uid, [pricelist_id], procurement.product_id.id, qty, partner_id, {'uom': uom_id})[pricelist_id]

            schedule_date = self._get_purchase_schedule_date(cr, uid, procurement, company, context=context)
            purchase_date = self._get_purchase_order_date(cr, uid, procurement, company, schedule_date, context=context)

            #Passing partner_id to context for purchase order line integrity of Line name
            new_context = context.copy()
            new_context.update({'lang': partner.lang, 'partner_id': partner_id})

            product = prod_obj.browse(cr, uid, procurement.product_id.id, context=new_context)
            taxes_ids = procurement.product_id.supplier_taxes_id
            taxes = acc_pos_obj.map_tax(cr, uid, partner.property_account_position, taxes_ids)

            name = product.partner_ref
            if product.description_purchase:
                name += '\n'+ product.description_purchase
            line_vals = {
                'name': name,
                'product_qty': qty,
                'product_id': procurement.product_id.id,
                'product_uom': uom_id,
                'price_unit': price or 0.0,
                'date_planned': schedule_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                'move_dest_id': res_id,
                'taxes_id': [(6,0,taxes)],
            }

            #Update an existing purchase order
            po_exists = self._planned_purchases_get_purchases(cr, uid, procurement, po_ids, context=context)

            if po_exists:
                purchase_id = po_exists[0]
                line_vals.update({'order_id': purchase_id})
                purchase_line_id = po_line_obj.create(cr, uid, line_vals)
                res[procurement.id] = purchase_id
                purchase = po_obj.browse(cr, uid, purchase_id, context=context)
                new_origin = (purchase.origin and (purchase.origin + ' ') or '') + (procurement.origin or '')
                po_obj.write(cr, uid, purchase_id, {'origin': new_origin}, context=context)
                self.message_post(cr, uid, [procurement.id], body=_("Merged into existing Purchase Order"), context=context)
            else:
                name = seq_obj.get(cr, uid, 'purchase.order') or _('PO: %s') % procurement.name
                po_vals = {
                    'name': name,
                    'origin': procurement.origin,
                    'partner_id': partner_id,
                    'location_id': procurement.location_id.id,
                    'warehouse_id': self._get_warehouse(procurement, company),
                    'pricelist_id': pricelist_id,
                    'date_order': purchase_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                    'company_id': procurement.company_id.id,
                    'fiscal_position': partner.property_account_position and partner.property_account_position.id or False,
                    'payment_term_id': partner.property_supplier_payment_term.id or False,
                }
                purchase_id = self.create_procurement_purchase_order(cr, uid, procurement, po_vals, line_vals, context=new_context)
                res[procurement.id] = purchase_id
                self.message_post(cr, uid, [procurement.id], body=_("Draft Purchase Order created"), context=context)
            self.write(cr, uid, [procurement.id], {'state': 'running', 'purchase_id': purchase_id})
        return res

procurement_order()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
