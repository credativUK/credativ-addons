# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution   
#    Copyright (C) 2015 credativ Ltd (<http://credativ.co.uk>).
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

from osv import osv, fields
from tools.translate import _
from datetime import datetime, timedelta
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
import netsvc

class SaleProcurementForecast(osv.osv):
    _name = "sale.procurement.forecast"
    _description = "Sale Procurement Forecast"
    _inherit = ['mail.thread']

    _columns = {
        'name': fields.char('Name', readonly=True, states={'draft':[('readonly',False)]}, required=True),
        'company_id': fields.many2one('res.company', 'Company', required=True, readonly=True, states={'draft':[('readonly',False)]}),
        'product_ids': fields.many2many('product.product', 'sale_procurement_forecast_product_rel', 'product_id', 'forecast_id', 'Products', domain=[('type', '=', 'product')],
                                        states={'draft':[('readonly',False)]}, readonly=True, help="Products included in this forecast, blank for all products"),
        'shop_ids': fields.many2many('sale.shop', 'sale_procurement_forecast_shop_rel', 'shop_id', 'forecast_id', 'Shops',
                                     states={'draft':[('readonly',False)]}, readonly=True, help="Shops included in this forecast, blank for all shops"),
        'warehouse_id': fields.many2one('stock.warehouse', 'Warehouse', readonly=True, states={'draft':[('readonly',False)]}, required=True),
        'date_start': fields.date('Start Date', help="Sale orders on or after this date will be included", required=True, readonly=True, states={'draft':[('readonly',False)]}),
        'date_stop': fields.date('End Date', help="Sale orders before this date will be included. Orders made on this date will NOT be included.", required=True, readonly=True, states={'draft':[('readonly',False)]}),
        'days': fields.integer('Supply Days', readonly=True, states={'draft':[('readonly',False)]}),
        'state': fields.selection([('draft','Draft'), ('confirm','Confirmed'), ('done','Done'), ('cancel','Cancelled')], 'Status', readonly=True),
        'forecast_line_ids': fields.one2many('sale.procurement.forecast.line', 'forecast_id', 'Sale Procurement Forecast Lines', states={'confirm':[('readonly',False)]}, readonly=True, copy=False),
    }

    _defaults = {
        'name': lambda self,cr,uid,context={}: self.pool.get('ir.sequence').get(cr, uid, 'sale.procurement.forecast'),
        'date_stop': lambda self,cr,uid,context={}: context.get('date', fields.date.context_today(self,cr,uid,context=context)),
        'days': 70,
        'company_id': lambda s, cr, uid, c: s.pool.get('res.company')._company_default_get(cr, uid, 'sale.procurement.forecast', context=c),
        'state': 'draft',
    }

    _sql_constraints = [
        ('name_forecast_uniq', 'unique (name,company_id)', 'The name of the sale procurement forecast must be unique per company !')
    ]

    def onchange_company_id(self, cr, uid, ids, company_id):
        value = {}
        warehouse_ids = self.pool.get('stock.warehouse').search(cr, uid, [('company_id', '=', company_id)])
        if warehouse_ids:
            value.update({'warehouse_id': warehouse_ids[0]})
        return {'value': value}

    def onchange_days_date_stop(self, cr, uid, ids, date_start, date_stop, days):
        value = {}
        if not date_stop:
            return {}
        date_stop = datetime.strptime(date_stop, DEFAULT_SERVER_DATE_FORMAT)
        new_date_start = (date_stop - timedelta(days=days or 0.0)).strftime(DEFAULT_SERVER_DATE_FORMAT)
        if date_start != new_date_start:
            value.update({'date_start': new_date_start})
        return {'value': value}

    def onchange_date_start(self, cr, uid, ids, date_start, date_stop, days):
        value = {}
        if not date_start or not date_stop:
            return {}
        date_start = datetime.strptime(date_start, DEFAULT_SERVER_DATE_FORMAT)
        date_stop = datetime.strptime(date_stop, DEFAULT_SERVER_DATE_FORMAT)
        new_days = (date_stop - date_start).days
        if days != new_days:
            value.update({'days': new_days})
        return {'value': value}

    def copy_data(self, cr, uid, id, default=None, context=None):
        if default is None:
            default = {}
        default = default.copy()
        forecast = self.browse(cr, uid, id, context=context)

        all_defaults = self.default_get(cr, uid, ['name', 'date_stop', 'state'], context=context)
        default.update(all_defaults)
        default['forecast_line_ids'] = []
        default['date_start'] = (datetime.strptime(default['date_stop'], DEFAULT_SERVER_DATE_FORMAT) - timedelta(days=forecast.days)).strftime(DEFAULT_SERVER_DATE_FORMAT)

        return super(SaleProcurementForecast, self).copy_data(cr, uid, id, default=default, context=context)

    def action_confirm(self, cr, uid, ids, context=None):
        product_obj = self.pool.get('product.product')
        shop_obj = self.pool.get('sale.shop')
        sale_line_obj = self.pool.get('sale.order.line')
        uom_obj = self.pool.get('product.uom')

        forecast_line_obj = self.pool.get('sale.procurement.forecast.line')

        for forecast in self.browse(cr, uid, ids, context=context):
            shop_ids = [x.id for x in forecast.shop_ids] or shop_obj.search(cr, uid, [('company_id', '=', forecast.company_id.id)], context=context)
            product_ids = [x.id for x in forecast.product_ids] or product_obj.search(cr, uid, [('type', '=', 'product')], context=context)

            ctx = context.copy()
            ctx.update({'warehouse': forecast.warehouse_id.id})
            if 'location' in ctx:
                del ctx['location']
            if 'shop' in ctx:
                del ctx['shop']

            product_datas = product_obj.read(cr, uid, product_ids, ['virtual_available', 'uom_id'], context=context)

            for product_data in product_datas:
                product_id = product_data['id']
                qty_virtual = product_data['virtual_available']
                qty_sold = 0
                uom_id = product_data['uom_id'][0]
                sale_line_ids = sale_line_obj.search(cr, uid, [('order_id.date_order', '>=', forecast.date_start),
                                                               ('order_id.date_order', '<', forecast.date_stop),
                                                               ('order_id.state', 'not in', ('draft', 'cancel')),
                                                               ('product_id', '=', product_id),
                                                               ], context=context)
                sale_line_datas = sale_line_obj.read(cr, uid, sale_line_ids, ['product_uom', 'product_uom_qty'], context=context)
                for sale_line_data in sale_line_datas:
                    converted_qty = uom_obj._compute_qty(cr, uid, sale_line_data['product_uom'][0], sale_line_data['product_uom_qty'], uom_id)
                    qty_sold += converted_qty
                qty_sold_avg = forecast.days and (qty_sold / forecast.days) or 0.0
                date_end = (datetime.strptime(forecast.date_stop, DEFAULT_SERVER_DATE_FORMAT) + timedelta(days=forecast.days)).strftime(DEFAULT_SERVER_DATE_FORMAT)
                qty_order = max([0.0, (qty_sold_avg * forecast.days) - qty_virtual])

                line_data = {
                    'forecast_id': forecast.id,
                    'product_id': product_id,
                    'uom_id': uom_id,
                    'qty_sold': qty_sold,
                    'qty_sold_avg': qty_sold_avg,
                    'qty_virtual': qty_virtual,
                    'date_end': date_end,
                    'qty_order': qty_order,
                }
                forecast_line_obj.create(cr, uid, line_data, context=context)
        self.write(cr, uid, ids, {'state': 'confirm'}, context=context)
        return True

    def action_done(self, cr, uid, ids, context=None):
        product_obj = self.pool.get('product.product')
        shop_obj = self.pool.get('sale.shop')
        sale_line_obj = self.pool.get('sale.order.line')
        uom_obj = self.pool.get('product.uom')
        proc_obj = self.pool.get('procurement.order')
        wkf_service = netsvc.LocalService('workflow')

        forecast_line_obj = self.pool.get('sale.procurement.forecast.line')

        for forecast in self.browse(cr, uid, ids, context=context):
            for line in forecast.forecast_line_ids:
                if line.qty_order <= 0.0:
                    continue
                proc_vals = {
                    'name': forecast.name,
                    'origin': forecast.name,
                    'date_planned': forecast.date_stop,
                    'product_id': line.product_id.id,
                    'product_qty': line.qty_order,
                    'product_uom': line.uom_id.id,
                    'product_uos_qty': line.qty_order,
                    'product_uos': line.uom_id.id,
                    'location_id': forecast.warehouse_id.lot_stock_id.id,
                    'procure_method': 'make_to_order',
                    'move_id': False,
                    'company_id': forecast.company_id.id,
                    'note': forecast.name,
                }
                proc_id = proc_obj.create(cr, uid, proc_vals, context=context)
                line.write({'procurement_id': proc_id}, context=context)
                wkf_service.trg_validate(uid, 'procurement.order', proc_id, 'button_confirm', cr)
                wkf_service.trg_validate(uid, 'procurement.order', proc_id, 'button_check', cr)

        self.write(cr, uid, ids, {'state': 'done'}, context=context)
        return True

    def action_draft(self, cr, uid, ids, context=None):
        forecast_line_obj = self.pool.get('sale.procurement.forecast.line')
        forecast_line_ids = forecast_line_obj.search(cr, uid, [('forecast_id', 'in', ids)], context=context)
        if forecast_line_ids:
            forecast_line_obj.unlink(cr, uid, forecast_line_ids)
        self.write(cr, uid, ids, {'state': 'draft'}, context=context)
        return True

    def action_cancel(self, cr, uid, ids, context=None):
        forecast_line_obj = self.pool.get('sale.procurement.forecast.line')
        forecast_line_ids = forecast_line_obj.search(cr, uid, [('forecast_id', 'in', ids)], context=context)
        if forecast_line_ids:
            forecast_line_obj.unlink(cr, uid, forecast_line_ids)
        self.write(cr, uid, ids, {'state': 'cancel'}, context=context)
        return True

    def unlink(self, cr, uid, ids, context=None):
        for forecast in self.browse(cr, uid, ids, context=context):
            if forecast.state == 'done':
                raise osv.except_osv(_('Warning!'), _('You cannot remove a completed forecast.'))
        return super(SaleProcurementForecast, self).unlink(cr, uid, ids, context=context)

class SaleProcurementForecastLine(osv.osv):
    _name = "sale.procurement.forecast.line"
    _description = "Sale Procurement Forecast Line"
    _rec_name = 'product_id'

    def _qty_sales_future(self, cr, uid, ids, name, arg, context=None):
        res = {id: 0 for id in ids}
        for line in self.browse(cr, uid, ids, context=context):
            date_begin = datetime.strptime(line.date_begin, DEFAULT_SERVER_DATE_FORMAT)
            date_end = datetime.strptime(line.date_end, DEFAULT_SERVER_DATE_FORMAT)
            days = (date_end - date_begin).days
            res[line.id] = line.qty_sold_avg * days
        return res

    _columns = {
        'forecast_id': fields.many2one('sale.procurement.forecast', 'Forecast', required=True, readonly=True),
        'product_id': fields.many2one('product.product', 'Product', required=True, readonly=True),
        'uom_id': fields.many2one('product.uom', 'UoM', readonly=True, required=True),
        'qty_sold': fields.float('Sold for Dates', readonly=True),
        'qty_sold_avg': fields.float('Average Sold by Day', readonly=True),
        'qty_virtual': fields.float('Virtual Stock', readonly=True),
        'date_begin': fields.related('forecast_id', 'date_stop', type="date", string='Cover Sales from Date', readonly=True, required=True),
        'date_end': fields.date('Cover Sales to Date', required=True),
        'qty_sales_future': fields.function(_qty_sales_future, string='Future Sales', type='float', readonly=True),
        'qty_order': fields.float('Stock to Order'),
        'procurement_id': fields.many2one('procurement.order', 'Procurement', readonly=True),
        'procurement_state': fields.related('procurement_id', 'state', type="selection", selection=[
            ('draft','Draft'),
            ('cancel','Cancelled'),
            ('confirmed','Confirmed'),
            ('exception','Exception'),
            ('running','Running'),
            ('ready','Ready'),
            ('done','Done'),
            ('waiting','Waiting')], string='Procurement State', readonly=True),
    }

    def onchange_date_end(self, cr, uid, ids, date_begin, date_end, qty_sold_avg, qty_virtual):
        value = {}
        if not date_begin:
            return {}
        date_begin = datetime.strptime(date_begin, DEFAULT_SERVER_DATE_FORMAT)
        date_end = datetime.strptime(date_end, DEFAULT_SERVER_DATE_FORMAT)
        days = (date_end - date_begin).days

        if date_end < date_begin:
            date_end = date_begin
            days = 0
            value.update({'date_end': date_begin})

        qty_sales_future = qty_sold_avg * days
        qty_order = max([0.0, qty_sales_future - qty_virtual])

        value.update({'qty_sales_future': qty_sales_future, 'qty_order': qty_order})
        return {'value': value}

    def open_procurement(self, cr, uid, ids, context=None):
        for line in self.browse(cr, uid, ids, context=context):
            if line.procurement_id:
                return {
                        'name': "Procurement Order",
                        'view_mode': 'form,tree',
                        'view_type': 'form',
                        'res_model': 'procurement.order',
                        'type': 'ir.actions.act_window',
                        'res_id': line.procurement_id.id,
                        'nodestroy': True,
                        'target': 'new',
                }
        return {}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
