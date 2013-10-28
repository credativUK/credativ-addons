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

class sale_order(osv.osv):
    _inherit = 'sale.order'

    def _fnct_requested_delivery_dates(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        # Return True if any lines have requested_delivery_date set
        for order in self.browse(cr, uid, ids, context=context):
            res[order.id] = False
            for line in order.order_line:
                if line.requested_delivery_date:
                    res[order.id] = True
                    continue
        return res

    _columns = { 
        'requested_delivery_dates': fields.function(_fnct_requested_delivery_dates, string='Requested Delivery Dates', type='bool', help="Do any lines have requested delivery dates set?", readonly=True),
    }

sale_order()

class sale_order_line(osv.osv):
    _inherit = 'sale.order.line'

    def _fnct_days_until_delivery(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for line in self.browse(cr, uid, ids, context=context):
            try:
                date_confirm = line.order_id.date_confirm and datetime.datetime.strptime(line.order_id.date_confirm, '%Y-%m-%d')
                timedelta_until_delivery = line.requested_delivery_date and datetime.datetime.strptime(line.requested_delivery_date, '%Y-%m-%d') - ( date_confirm or datetime.datetime.now() )
                days_until_delivery = timedelta_until_delivery and timedelta_until_delivery.days + 1 # Add one because of rounding
                res[line.id] = days_until_delivery
            except:
                res[line.id] = False
        return res

    def _fnct_default_delivery_date(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for line in self.browse(cr, uid, ids, context=context):
            try:
                date_confirm = line.order_id.date_confirm and datetime.datetime.strptime(line.order_id.date_confirm, '%Y-%m-%d')
                default_delivery_datetime = datetime.timedelta(days=line.delay) + ( date_confirm or datetime.datetime.now() )
                res[line.id] =  default_delivery_datetime.strftime('%Y-%m-%d')
            except:
                res[line.id] = False
        return res

    def onchange_requested_delivery_date(self, cr, uid, ids, requested_delivery_date, default_delivery_date, context=None):
        if not context:
            context = {}
        
        res = {}
        new_days_until_delivery = False
        if requested_delivery_date:
            line = self.browse(cr, uid, ids, context=context)[0]
            original_date = line.requested_delivery_date and datetime.datetime.strptime(line.requested_delivery_date, '%Y-%m-%d') or datetime.datetime.today()
            days_change =  ( datetime.datetime.strptime(requested_delivery_date, '%Y-%m-%d') - original_date ).days
            new_days_until_delivery = (line.days_until_delivery or 0) + days_change
            if requested_delivery_date < default_delivery_date:
                res['warning'] = {'title':'Requested days until delivery is less than delivery lead time', 'message':'Please ensure this delivery date is manageable before continuing.'}
        res['value'] = {'days_until_delivery': new_days_until_delivery }
        
        return res

    def button_confirm(self, cr, uid, ids, context=None):
        if not context:
            context = {}
        res = super(sale_order_line, self).button_confirm(cr, uid, ids, context=context)
        for line in self.browse(cr, uid, ids, context=context):
            if line.days_until_delivery:
                self.write(cr, uid, ids, {'delay': line.days_until_delivery})
        return res

    _columns = { 
        'days_until_delivery': fields.function(_fnct_days_until_delivery, string='Days Until Delivery', type='float', help="Number of days remaining until requested delivery date.", readonly=True),
        'requested_delivery_date': fields.date('Requested Delivery Date', select=True, help="Date on which customer has requested delivery."),
        'default_delivery_date': fields.function(_fnct_default_delivery_date, string='Default Delivery Date', type='date', help="Date on which delivery is projected, assuming customer has not requested a specific date."),
    }
    _defaults = {
        'requested_delivery_date': False,
    }

sale_order_line()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
