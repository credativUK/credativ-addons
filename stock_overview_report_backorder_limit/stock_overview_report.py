# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 credativ ltd (<http://www.credativ.co.uk>).
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
            'supplier_virtual_available',
            'supplier_virtual_available_combined',
        ]))  # Add
        return list(res)

    def _prepare_data_line(self, cr, uid, data, default=None):
        if default is None:
            default = {}
        res = super(StockOverviewReport, self)._prepare_data_line(
            cr, uid, data, default=default)
        res.update({
            'supplier_virtual_available':
                data.get('supplier_virtual_available'),
            'supplier_virtual_available_combined':
                data.get('supplier_virtual_available_combined'),
        })
        return res


class StockOverviewReportLine(osv.osv_memory):
    _inherit = 'stock.overview.report.line'

    _columns = {
        'supplier_virtual_available': fields.float(
            'Supplier Available Quantity',
            digits_compute=dp.get_precision('Product Unit of Measure'),
            help="Forecast quantity (computed as Quantity On Hand "
                 "- Outgoing + Incoming) at the virtual supplier location "
                 "for the current warehouse if applicable, otherwise 0."),
        'supplier_virtual_available_combined': fields.float(
            'Available Quantity inc. Supplier',
            digits_compute=dp.get_precision('Product Unit of Measure'),
            help="Forecast quantity (computed as Quantity On Hand "
                 "- Outgoing + Incoming) at the virtual supplier location "
                 "for the current warehouse if applicable, otherwise 0, plus "
                 "the normal forecast quantity."),
    }
