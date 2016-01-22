# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2016 credativ ltd (<http://www.credativ.co.uk>).
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

from openerp.osv import fields, osv
import openerp.addons.decimal_precision as dp


class StockOverviewReport(osv.osv_memory):
    _inherit = 'stock.overview.report'

    def _get_report_fields(self):
        res = set(super(StockOverviewReport, self)._get_report_fields())
        res.update(set([
            'standard_price',
        ]))  # Add
        return list(res)

    def _prepare_data_line(self, cr, uid, data, default=None):
        if default is None:
            default = {}
        res = super(StockOverviewReport, self)._prepare_data_line(
            cr, uid, data, default=default)
        res.update({
            'total_price':
                data.get('standard_price') * data.get('qty_available'),
        })
        return res

    def _get_sql(self, cr, uid, ids, wizard, context=None):
        if context is None:
            context = {}

        field_names, insert_query, insert_params, with_query, with_params, select_query, select_params, from_query = super(StockOverviewReport, self)._get_sql(cr, uid, ids, wizard, context=None)

        field_names.append('total_price')
        insert_query = " INSERT INTO stock_overview_report_line (" + ",".join(field_names) + ")"

        select_query += """, (COALESCE(in_done.product_qty, 0.0) - COALESCE(out_done.product_qty, 0.0)) * COALESCE(pt.standard_price, 0.0) total_price"""
        select_params.extend([])

        return field_names, insert_query, insert_params, with_query, with_params, select_query, select_params, from_query

class StockOverviewReportLine(osv.osv_memory):
    _inherit = 'stock.overview.report.line'

    _columns = {
        'total_price': fields.float(
            'Total Price',
            digits_compute=dp.get_precision('Purchase Price'),
            help="The current cost price multipled by available quantity for the selected date. " \
            "This will give inaccurate values for historical dates since it will only use the " \
            "current cost price."),
    }
