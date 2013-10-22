# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution   
#    Copyright (C) 2013 credativ Ltd (<http://credativ.co.uk>).
#    All Rights Reserved
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

from osv import osv, fields
import datetime

class stock_dispatch(osv.osv):
    _inherit = 'stock.dispatch'

    _columns = {
        'dispatch_trigger_date': fields.datetime('Dispatch Trigger Date', help="Date when dispatch actions are triggered."),
        }

    def action_done(self, cr, uid, ids, context=None):
        res = super(stock_dispatch, self).action_done(cr, uid, ids, context=context)
        if res:
            holiday_pool = self.pool.get('hr.holidays')
            for dispatch in self.browse(cr, uid, ids, context=context):
                dispatch_action_delay = dispatch.carrier_id and dispatch.carrier_id.dispatch_action_delay or 0
                country = context.get('country_id', False)
                if not country:
                    shop = dispatch.stock_moves and dispatch.stock_moves[0].sale_line_id and dispatch.stock_moves[0].sale_line_id.order_id and dispatch.stock_moves[0].sale_line_id.order_id.shop_id
                    country = shop and shop.address_id and shop.address_id.country_id and shop.address_id.country_id.id
                if not country:
                    order = dispatch.stock_moves and dispatch.stock_moves[0].sale_line_id and dispatch.stock_moves[0].sale_line_id.order_id
                    country = order and order.partner_shipping_id and order.partner_shipping_id.country_id and order.partner_shipping_id.country_id.id
                if country:
                    # Skip weekends and holidays if the country is defined in context
                    days = int(dispatch_action_delay) / 24
                    extra_hours = int(dispatch_action_delay) % 24
                    dispatch_trigger_date = datetime.datetime.strptime(dispatch.complete_date, '%Y-%m-%d %H:%M:%S')
                    dispatch_trigger_hours = dispatch_trigger_date.hour
                    dispatch_trigger_day = dispatch_trigger_date.strftime('%Y-%m-%d')
                    for day in range(days):
                        dispatch_trigger_day = holiday_pool.nextWorkingDays(cr, uid, dispatch_trigger_day, country=country, no_of_days=1, context=context)[0]
                    if extra_hours:
                        dispatch_trigger_hours += extra_hours
                        if dispatch_trigger_hours >= 24:
                            dispatch_trigger_day = holiday_pool.nextWorkingDays(cr, uid, dispatch_trigger_day, country=country, no_of_days=1, context=context)[0]
                            dispatch_trigger_hours -= 24
                    dispatch_trigger_date = datetime.datetime.strptime(dispatch_trigger_day, '%Y-%m-%d') + datetime.timedelta(hours=dispatch_trigger_hours, minutes=dispatch_trigger_date.minute, seconds=dispatch_trigger_date.second)
                else:
                    # Simply add action delay to dispatch completion date if no country defined in context
                    dispatch_trigger_date = datetime.datetime.strptime(dispatch.complete_date, '%Y-%m-%d %H:%M:%S') + datetime.timedelta(hours=dispatch_action_delay)
                
                dispatch_trigger_date = dispatch_trigger_date.strftime('%Y-%m-%d %H:%M:%S')
                self.write(cr, uid, [dispatch.id], {'dispatch_trigger_date': dispatch_trigger_date}, context=context)
        return res

stock_dispatch()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
