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

    def _get_sql(self, cr, uid, ids, wizard, context=None):
        if context is None:
            context = {}

        field_names, insert_query, insert_params, with_query, with_params, select_query, select_params, from_query = super(StockOverviewReport, self)._get_sql(cr, uid, ids, wizard, context=None)

        field_names.extend(['supplier_virtual_available',
                            'supplier_virtual_available_combined'])
        insert_query = " INSERT INTO stock_overview_report_line (" + ",".join(field_names) + ")"
        insert_params = []

        with_where_query = ""
        if wizard.date:
            with_where_query = " AND sm.date < %s "
        with_query += """, stock_incoming_supplier AS (
                            SELECT
                                sm.product_id,
                                SUM(sm.product_qty) product_qty,
                                sw.id warehouse_id
                            FROM stock_warehouse sw
                            INNER JOIN stock_move sm
                                ON sm.location_dest_id IN (SELECT child_id FROM locations WHERE parent_id = sw.lot_supplier_virtual_id)
                                AND sm.location_id NOT IN (SELECT child_id FROM locations WHERE parent_id = sw.lot_supplier_virtual_id)
                                AND sm.state IN ('done', 'confirmed', 'assigned', 'waiting')
                                """+with_where_query+"""
                            GROUP BY sm.product_id, sw.id
                        ), stock_outgoing_supplier AS (
                            SELECT
                                sm.product_id,
                                SUM(sm.product_qty) product_qty,
                                sw.id warehouse_id
                            FROM stock_warehouse sw
                            INNER JOIN stock_move sm
                                ON sm.location_dest_id NOT IN (SELECT child_id FROM locations WHERE parent_id = sw.lot_supplier_virtual_id)
                                AND sm.location_id IN (SELECT child_id FROM locations WHERE parent_id = sw.lot_supplier_virtual_id)
                                AND sm.state IN ('done', 'confirmed', 'assigned', 'waiting')
                                """+with_where_query+"""
                            GROUP BY sm.product_id, sw.id
                        )"""
        if wizard.date:
            with_params.extend([wizard.date, wizard.date])

        select_query += """, COALESCE(in_supplier.product_qty, 0.0)
                - COALESCE(out_supplier.product_qty, 0.0) supplier_virtual_available,
            COALESCE(in_supplier.product_qty, 0.0)
                - COALESCE(out_supplier.product_qty, 0.0)
                + COALESCE(in_done.product_qty, 0.0)
                - COALESCE(out_done.product_qty, 0.0)
                + COALESCE(in_pending.product_qty, 0.0)
                - COALESCE(out_pending.product_qty, 0.0) supplier_virtual_available_combined"""
        select_params.extend([])

        from_query += """ LEFT OUTER JOIN stock_incoming_supplier in_supplier ON in_supplier.product_id = pp.id AND in_supplier.warehouse_id = sw.id
                        LEFT OUTER JOIN stock_outgoing_supplier out_supplier ON out_supplier.product_id = pp.id AND out_supplier.warehouse_id = sw.id """

        return field_names, insert_query, insert_params, with_query, with_params, select_query, select_params, from_query

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
