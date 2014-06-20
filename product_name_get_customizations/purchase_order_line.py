# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2014 credativ Ltd (<http://credativ.co.uk>).
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

from openerp.osv import osv

class PurchaseOrderLine(osv.Model):
    _inherit = 'purchase.order.line'

    def onchange_product_id(self, cr, uid, ids, pricelist_id, product_id, qty, uom_id,
            partner_id, date_order=False, fiscal_position_id=False, date_planned=False,
            name=False, price_unit=False, context=None):
        result = super(PurchaseOrderLine, self).onchange_product_id(cr, uid, ids, pricelist_id, product_id, qty, uom_id,
            partner_id, date_order=date_order, fiscal_position_id=fiscal_position_id, date_planned=date_planned,
            name=name, price_unit=price_unit, context=context)
        if product_id and 'value' in result and 'name' in result['value']:
            partner_obj = self.pool.get('res.partner')
            product_obj = self.pool.get('product.product')
            if partner_id:
                lang = partner_obj.browse(cr, uid, partner_id).lang
            context_partner = {'lang': lang, 'partner_id': partner_id, 'product_display_format': 'name'}
            product_obj = product_obj.browse(cr, uid, product_id, context=context_partner)
            result['value']['name'] = self.pool.get('product.product').name_get(cr, uid, [product_obj.id], context=context_partner)[0][1]
            if product_obj.description_purchase:
                result['value']['name'] += '\n'+product_obj.description_purchase
        return result

    product_id_change = onchange_product_id