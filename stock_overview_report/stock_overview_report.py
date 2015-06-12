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

from openerp.osv import fields, osv
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
from openerp.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT
from datetime import datetime
import pytz

class StockOverviewReport(osv.osv_memory):
    _name = 'stock.overview.report'
    _description = "Stock Overview Report"
    _rec_name = 'date'
    _transient_max_hours = 12.0
    _transient_max_count = 0.0

    _columns = {
        'date': fields.datetime('Stock level date', help='The date the stock levels will be taken for. Leave blank to use the current date and time.'),
        'line_ids': fields.one2many('stock.overview.report.line', 'wizard_id', 'Stock Overview Report Lines'),
     }

    def _get_report_fields(self):
        return ['uom_id', 'qty_available', 'virtual_available', 'incoming_qty', 'outgoing_qty', 'categ_id']

    def _prepare_data_line(self, cr, uid, data, default=None):
        if default is None:
            default = {}
        res = {}
        res.update(default)
        res.update({
                'product_id': data['id'],
                'uom_id': data.get('uom_id', [None,])[0],
                'categ_id': data.get('categ_id', [None,])[0],
                'qty_available': data.get('qty_available'),
                'virtual_available': data.get('virtual_available'),
                'incoming_qty': data.get('incoming_qty'),
                'outgoing_qty': data.get('outgoing_qty'),
            })
        return res

    def populate_lines(self, cr, uid, ids, context=None):
        if context is None:
            context = {}

        company_obj = self.pool.get('res.company')
        warehouse_obj = self.pool.get('stock.warehouse')
        product_obj = self.pool.get('product.product')
        line_obj = self.pool.get('stock.overview.report.line')

        res = {'type': 'ir.actions.act_window_close'}

        for wizard in self.browse(cr, uid, ids, context=context):
            if wizard.line_ids:
                line_obj.unlink(cr, uid, [x.id for x in wizard.line_ids], context=context)

            user = self.pool.get("res.users").read(cr, uid, uid, ['partner_id'], context=context)
            user_timezone = self.pool.get("res.partner").read(cr, uid, user['partner_id'][0],['tz'], context=context)['tz']
            if not user_timezone:
                user_timezone = 'UTC'
            if wizard.date:
                date = datetime.strptime(wizard.date, DEFAULT_SERVER_DATETIME_FORMAT)
                local_date = pytz.utc.localize(date, is_dst=None).astimezone(pytz.timezone(user_timezone))
            else:
                local_date = datetime.now(pytz.timezone(user_timezone))
            for company_id in company_obj.search(cr, uid, [], context=context):
                for warehouse_id in warehouse_obj.search(cr, uid, [('company_id', '=', company_id),], context=context):
                    ctx = context.copy()
                    ctx.update({'shop': False, 'warehouse': warehouse_id, 'location': False,
                                'to_date': wizard.date or False})
                    product_ids = product_obj.search(cr, uid, [], context=context)
                    for product in product_obj.read(cr, uid, product_ids, self._get_report_fields(), context=ctx):
                        data = self._prepare_data_line(cr, uid, product, {
                                'wizard_id': wizard.id,
                                'company_id': company_id,
                                'warehouse_id': warehouse_id,
                            })
                        line_obj.create(cr, uid, data, context=context)

            cr.execute('select id from ir_ui_view where model=%s and type=%s', ('stock.overview.report.line', 'tree'))
            view_ids = cr.fetchone()
            view_id = view_ids and view_ids[0] or False

            cr.execute('select id from ir_ui_view where model=%s and type=%s', ('stock.overview.report.line', 'search'))
            search_ids = cr.fetchone()
            search_id = search_ids and search_ids[0] or False

            res = {
                'domain': "[('wizard_id','=',%d)]" % (wizard.id,),
                'name': _('Stock Overview Report for %s - %s') % (local_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT), user_timezone),
                'view_type': 'form',
                'view_mode': 'tree',
                'res_model': 'stock.overview.report.line',
                'views': [(view_id, 'tree'),],
                'search_view_id': search_id,
                'type': 'ir.actions.act_window',
                'nodestroy': True,
                'limit': 100000,
                'context': '{"search_default_has_stock": True, "product_display_format": "code", "search_default_group_company_id": True, "search_default_group_category_id": True, "search_default_group_warehouse_id": True}',
            }
        return res

class StockOverviewReportLine(osv.osv_memory):
    _name = 'stock.overview.report.line'
    _description = "Stock Overview Report Line"
    _rec_name = 'product_id'
    _transient_max_hours = 12.0
    _transient_max_count = 0.0

    _columns = {
        'wizard_id': fields.many2one('stock.overview.report', 'Stock Overview Report'),
        'product_id': fields.many2one('product.product', 'Product'),
        'categ_id': fields.many2one('product.category', string='Primary Category', readonly=True),
        'categ_ids': fields.related('product_id', 'categ_ids', type='many2many', relation='product.category', string='Product Categories', readonly=True),
        'company_id': fields.many2one('res.company', 'Company'),
        'warehouse_id': fields.many2one('stock.warehouse', 'Warehouse'),
        'uom_id': fields.many2one('product.uom', 'UoM'),
        'qty_available': fields.float('Quantity On Hand', digits_compute=dp.get_precision('Product Unit of Measure'),
            help="Current quantity of products.\n"
                 "In a context with a single Stock Location, this includes "
                 "goods stored at this Location, or any of its children.\n"
                 "In a context with a single Warehouse, this includes "
                 "goods stored in the Stock Location of this Warehouse, or any "
                 "of its children.\n"
                 "In a context with a single Shop, this includes goods "
                 "stored in the Stock Location of the Warehouse of this Shop, "
                 "or any of its children.\n"
                 "Otherwise, this includes goods stored in any Stock Location "
                 "with 'internal' type."),
        'virtual_available': fields.float('Forecasted Quantity', digits_compute=dp.get_precision('Product Unit of Measure'),
            help="Forecast quantity (computed as Quantity On Hand "
                 "- Outgoing + Incoming)\n"
                 "In a context with a single Stock Location, this includes "
                 "goods stored in this location, or any of its children.\n"
                 "In a context with a single Warehouse, this includes "
                 "goods stored in the Stock Location of this Warehouse, or any "
                 "of its children.\n"
                 "In a context with a single Shop, this includes goods "
                 "stored in the Stock Location of the Warehouse of this Shop, "
                 "or any of its children.\n"
                 "Otherwise, this includes goods stored in any Stock Location "
                 "with 'internal' type."),
        'incoming_qty': fields.float('Incoming', digits_compute=dp.get_precision('Product Unit of Measure'),
            help="Quantity of products that are planned to arrive.\n"
                 "In a context with a single Stock Location, this includes "
                 "goods arriving to this Location, or any of its children.\n"
                 "In a context with a single Warehouse, this includes "
                 "goods arriving to the Stock Location of this Warehouse, or "
                 "any of its children.\n"
                 "In a context with a single Shop, this includes goods "
                 "arriving to the Stock Location of the Warehouse of this "
                 "Shop, or any of its children.\n"
                 "Otherwise, this includes goods arriving to any Stock "
                 "Location with 'internal' type."),
        'outgoing_qty': fields.float('Outgoing', digits_compute=dp.get_precision('Product Unit of Measure'),
            help="Quantity of products that are planned to leave.\n"
                 "In a context with a single Stock Location, this includes "
                 "goods leaving this Location, or any of its children.\n"
                 "In a context with a single Warehouse, this includes "
                 "goods leaving the Stock Location of this Warehouse, or "
                 "any of its children.\n"
                 "In a context with a single Shop, this includes goods "
                 "leaving the Stock Location of the Warehouse of this "
                 "Shop, or any of its children.\n"
                 "Otherwise, this includes goods leaving any Stock "
                 "Location with 'internal' type."),
    }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
