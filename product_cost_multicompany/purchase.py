# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2014 credativ ltd (<http://www.credativ.co.uk>). All Rights Reserved
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

#
# FIXME: Comment from the origional report:
# Please note that these reports are not multi-currency !!!
#

from osv import osv, fields
from openerp import tools

class PurchaseReport(osv.Model):
    _inherit = "purchase.report"

    def init(self, cr):
        tools.sql.drop_view_if_exists(cr, 'purchase_report')
        cr.execute("""
            create or replace view purchase_report as (
                select
                    min(l.id) as id,
                    s.date_order as date,
                    to_char(s.date_order, 'YYYY') as name,
                    to_char(s.date_order, 'MM') as month,
                    to_char(s.date_order, 'YYYY-MM-DD') as day,
                    s.state,
                    s.date_approve,
                    s.minimum_planned_date as expected_date,
                    s.dest_address_id,
                    s.pricelist_id,
                    s.validator,
                    s.warehouse_id as warehouse_id,
                    s.partner_id as partner_id,
                    s.create_uid as user_id,
                    s.company_id as company_id,
                    l.product_id,
                    t.categ_id as category_id,
                    t.uom_id as product_uom,
                    s.location_id as location_id,
                    sum(l.product_qty/u.factor*u2.factor) as quantity,
                    extract(epoch from age(s.date_approve,s.date_order))/(24*60*60)::decimal(16,2) as delay,
                    extract(epoch from age(l.date_planned,s.date_order))/(24*60*60)::decimal(16,2) as delay_pass,
                    count(*) as nbr,
                    sum(l.price_unit*l.product_qty)::decimal(16,2) as price_total,
                    avg(100.0 * (l.price_unit*l.product_qty) / NULLIF(coalesce(ppm.standard_price)*l.product_qty/u.factor*u2.factor, 0.0))::decimal(16,2) as negociation,
                    sum(coalesce(ppm.standard_price)*l.product_qty/u.factor*u2.factor)::decimal(16,2) as price_standard,
                    (sum(l.product_qty*l.price_unit)/NULLIF(sum(l.product_qty/u.factor*u2.factor),0.0))::decimal(16,2) as price_average
                from purchase_order_line l
                    join purchase_order s on (l.order_id=s.id)
                        left join product_product p on (l.product_id=p.id)
                            left join product_template t on (p.product_tmpl_id=t.id)
                                left join product_price_multi ppm on (ppm.product_id=t.id and ppm.company_id=s.company_id)
                    left join product_uom u on (u.id=l.product_uom)
                    left join product_uom u2 on (u2.id=t.uom_id)
                group by
                    s.company_id,
                    s.create_uid,
                    s.partner_id,
                    u.factor,
                    s.location_id,
                    l.price_unit,
                    s.date_approve,
                    l.date_planned,
                    l.product_uom,
                    s.minimum_planned_date,
                    s.pricelist_id,
                    s.validator,
                    s.dest_address_id,
                    l.product_id,
                    t.categ_id,
                    s.date_order,
                    to_char(s.date_order, 'YYYY'),
                    to_char(s.date_order, 'MM'),
                    to_char(s.date_order, 'YYYY-MM-DD'),
                    s.state,
                    s.warehouse_id,
                    u.uom_type,
                    u.category_id,
                    t.uom_id,
                    u.id,
                    u2.factor
            )
        """)

class PurchaseOrderLine(osv.Model):
    _inherit = 'purchase.order.line'

    def onchange_product_id(self, cr, uid, ids, pricelist_id, product_id, qty, uom_id,
            partner_id, date_order=False, fiscal_position_id=False, date_planned=False,
            name=False, price_unit=False, context=None):

        context = context or {}
        res = super(PurchaseOrderLine, self).onchange_product_id(cr, uid, ids, pricelist_id, product_id, qty, uom_id, partner_id,
                                                             date_order=date_order, fiscal_position_id=fiscal_position_id, date_planned=date_planned,
                                                             name=name, price_unit=price_unit, context=context)

        # Only get the default price_unit if we don't already have one and we are not getting it from the price list
        if 'price_unit' in res.get('value', {}) and not price_unit and not pricelist_id:
            # Take the company for the partner, or user if not set on partner
            company_id = res.pool.get('res.users').browse(cr, uid, uid).company_id.id
            if partner_id:
                partner = self.pool.get(cr, uid, partner_id).company_id.id or company_id
            product = self.pool.get('product.product').browse(cr, uid, product_id, context={'company_id': company_id})
            price = product.standard_price
            res.setdefault('value', {}).update({'price_unit': price})

        return res

    product_id_change = onchange_product_id

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
