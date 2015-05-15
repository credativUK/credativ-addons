# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2013 credativ Ltd (<http://credativ.co.uk>).
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

from openerp import tools
from openerp.osv import fields, osv

class sales_analysis_multi(osv.osv_memory):
    """
    For sales analysis report
    """
    _name = "sales.analysis.multi"
    _description = "Sales Analysis multi Wizard"
    _columns = {
        'currency_id': fields.many2one('res.currency', \
                                    'Select Report Currency',  \
                                    help='Select currency for which report needs to generate'),
        'date_from': fields.date('Start date'),
        'date_to': fields.date('End date'),
    }

    def _get_currency(self, cr, uid, context=None):
        """Return default  Currency value"""

        return self.pool.get('res.users').browse(cr,uid,uid).company_id.currency_id.id

    def sales_report_open_window(self, cr, uid, ids, context=None):
        """
        Opens Sales Analysis
        @param cr: the current row, from the database cursor,
        @param uid: the current user’s ID for security checks,
        @param ids: List of account chart’s IDs
        @return: dictionary of Sales analysis window on given fiscalyear and all Entries or posted entries
        """

        mod_obj = self.pool.get('ir.model.data')
        act_obj = self.pool.get('ir.actions.act_window')
        if context is None:
            context = {}
        data = self.read(cr, uid, ids, [], context=context)[0]
        result = mod_obj.get_object_reference(cr, uid, 'sale_analysis_multi', 'action_view_sale_report_multi')
        id = result and result[1] or False
        result = act_obj.read(cr, uid, [id], context=context)[0]
        if data['currency_id']:
            result['domain'] = str([('sales_currency_id', '=', data['currency_id'][0])])
            result['name'] += ':' + data['currency_id'][1]
            result['sales_currency_id'] = data['currency_id'][0]
        return result

    _defaults = {
        'currency_id': _get_currency,
    }

sales_analysis_multi()

class sale_report_multi(osv.osv):

    _name = "sale.report.multi"
    _description = "Sales Orders Statistics in other Currency"
    _auto = False
    _rec_name = 'date'

    _columns = {
        'date': fields.date('Date Order', readonly=True),
        'date_confirm': fields.date('Date Confirm', readonly=True),
        'year': fields.char('Year', size=4, readonly=True),
        'month': fields.selection([('01', 'January'), ('02', 'February'), ('03', 'March'), ('04', 'April'),
            ('05', 'May'), ('06', 'June'), ('07', 'July'), ('08', 'August'), ('09', 'September'),
            ('10', 'October'), ('11', 'November'), ('12', 'December')], 'Month', readonly=True),
        'day': fields.char('Day', size=128, readonly=True),
        'product_id': fields.many2one('product.product', 'Product', readonly=True),
        'product_uom': fields.many2one('product.uom', 'Unit of Measure', readonly=True),
        'product_uom_qty': fields.float('# of Qty', readonly=True),
        'partner_id': fields.many2one('res.partner', 'Partner', readonly=True),
        'shop_id': fields.many2one('sale.shop', 'Shop', readonly=True),
        'company_id': fields.many2one('res.company', 'Company', readonly=True),
        'user_id': fields.many2one('res.users', 'Salesperson', readonly=True),
        'price_total': fields.float('Total Price', readonly=True),
        'delay': fields.float('Commitment Delay', digits=(16,2), readonly=True),
        'categ_id': fields.many2one('product.category','Category of Product', readonly=True),
        'nbr': fields.integer('# of Lines', readonly=True),
        'pricelist_id': fields.many2one('product.pricelist', 'Pricelist', readonly=True),
        'analytic_account_id': fields.many2one('account.analytic.account', 'Analytic Account', readonly=True),
        'shipped': fields.boolean('Shipped', readonly=True),
        'shipped_qty_1': fields.integer('Shipped', readonly=True),
        'currency_total':fields.float('Total in currency', digits=(16,2), readonly=True),
        'sales_currency_id':fields.many2one('res.currency','Report Currency', readonly=True),
        'ship_date': fields.date('Date Order', readonly=True),
        'state': fields.selection([
            ('draft', 'Quotation'),
            ('waiting_date', 'Waiting Schedule'),
            ('manual', 'Manual In Progress'),
            ('progress', 'In Progress'),
            ('invoice_except', 'Invoice Exception'),
            ('done', 'Done'),
            ('cancel', 'Cancelled')
            ], 'Order Status', readonly=True),
    }

    def init(self, cr):
        tools.drop_view_if_exists(cr, 'sale_report_multi')
        cr.execute("""
            create or replace view sale_report_multi as (
                select
                    min(l.id) as id,
                    l.product_id as product_id,
                    t.uom_id as product_uom,
                    sum(l.product_uom_qty / u.factor * u2.factor) as product_uom_qty,
                    sum(l.product_uom_qty * l.price_unit * (100.0-l.discount) / 100.0) as price_total,
                    count(*) as nbr,
                    s.date_order as date,
                    s.date_confirm as date_confirm,
                    to_char(s.date_order, 'YYYY') as year,
                    to_char(s.date_order, 'MM') as month,
                    to_char(s.date_order, 'YYYY-MM-DD') as day,
                    s.partner_id as partner_id,
                    s.user_id as user_id,
                    s.shop_id as shop_id,
                    s.company_id as company_id,
                    extract(epoch from avg(date_trunc('day',s.date_confirm)-date_trunc('day',s.create_date)))/(24*60*60)::decimal(16,2) as delay,
                    t.categ_id as categ_id,
                    s.pricelist_id as pricelist_id,
                    s.project_id as analytic_account_id,
                    sm.date as ship_date,
                    c.id as sales_currency_id,
                    (sum(l.product_uom_qty * l.price_unit * (100.0-l.discount) / 100.0)/(cr_in.rate / cr.rate)) as currency_total
                from
                    sale_order_line l
                      join sale_order s on (l.order_id=s.id) 
                         left join product_product p on (l.product_id=p.id)
                            left join product_template t on (p.product_tmpl_id=t.id)
                    left join product_uom u on (u.id=l.product_uom)
                    left join product_uom u2 on (u2.id=t.uom_id)
                    left join product_pricelist pl on (pl.id = s.pricelist_id)
                    cross join res_currency c
                    left join res_currency_rate cr on (cr.currency_id = c.id)
                    left join res_currency_rate cr_in on (cr.currency_id = c.id)
                    inner join stock_move sm on (sm.sale_line_id = l.id)
                where
                    cr.id in (select id from res_currency_rate c_rate
                    where 
                    c_rate.currency_id = c.id and c_rate.name::timestamp with time zone <= sm.date::timestamp with time zone order by name DESC LIMIT 1)
                    and
                    cr_in.id in (select id from res_currency_rate c_rate
                    where
                    c_rate.currency_id = pl.currency_id and c_rate.name::timestamp with time zone <= sm.date::timestamp with time zone order by name DESC LIMIT 1)
                    and
                    sm.state in ('done')
                    and
                    c.active = 't'
                group by
                    l.product_id,
                    l.order_id,
                    t.uom_id,
                    t.categ_id,
                    s.date_order,
                    s.date_confirm,
                    s.partner_id,
                    s.user_id,
                    s.shop_id,
                    s.company_id,
                    s.pricelist_id,
                    s.project_id,
                    c.name,
                    cr.rate,
                    c.id,
                    cr_in.id,
                    sm.date
                order by c.id, l.product_id, l.order_id
            )
        """)

sale_report_multi()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
