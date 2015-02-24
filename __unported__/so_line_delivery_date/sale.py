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

    def write(self, cr, uid, ids, vals, context=None):
        if context is None:
            context = {}

        res = super(sale_order, self).write(cr, uid, ids, vals, context=context)

        id_list = isinstance(ids, list) and ids[:] or [ids]
        self_browses = self.browse(cr, uid, id_list, context=context)
        for self_browse in self_browses:
            if self_browse.requested_delivery_date and not self_browse.delivery_date_per_line:
                line_pool = self.pool.get('sale.order.line')
                lids = line_pool.search(cr, uid, [('order_id', '=', self_browse.id)], context=context)
                if lids:
                    line_pool.write(cr, uid, lids, {'requested_delivery_date' : self_browse.requested_delivery_date}, context=context)
        return res


    _columns = { 
        'requested_delivery_dates': fields.function(_fnct_requested_delivery_dates, string='Requested Delivery Dates', type='bool', help="Do any lines have requested delivery dates set?", readonly=True),
        'requested_delivery_date' : fields.date('Requested Delivery Date', select=True, help="Date on which customer has requested delivery."),
        'delivery_date_per_line':fields.related('company_id', 'delivery_date_per_line', type='boolean', relation='res.company', string='Delivery dates per-line.'), 
    }

sale_order()

class sale_order_line(osv.osv):
    _inherit = 'sale.order.line'

    def create(self, cr, uid, vals, context=None):
        if context is None:
            context = {}

        com = vals.get('company_id', False)
        if com:
            com_pool = self.pool.get('res.company')
            com_browse = com_pool.browse(cr, uid, com, context=context)
            if not com_browse.delivery_date_per_line:
                order_pool = self.pool.get('sale.order')
                order = order_pool.browse(cr, uid, vals.get('order_id'), context=context)
                vals.update({'requested_delivery_date' : order.requested_delivery_date})
        return super(sale_order_line, self).create(cr, uid, vals, context=context)

    def onchange_delay(self, cr, uid, ids, delay, context=None):
        context = context or {}
        res = {'value':{}}
        res['value']['default_delivery_date'] = self._get_single_default_delivery_date(cr, uid, ids and ids[0], delay=delay, context=context)
        return res

    def _get_single_days_until_delivery(self, cr, uid, id, requested_delivery_date, context=None):
        today = datetime.datetime(year=datetime.datetime.today().year, month=datetime.datetime.today().month, day=datetime.datetime.today().day)
        if requested_delivery_date and not id:
            timedelta_until_delivery = datetime.datetime.strptime(requested_delivery_date, '%Y-%m-%d') - today
            return timedelta_until_delivery.days
        try:
            line = self.browse(cr, uid, id, context=context)
            if not requested_delivery_date:
                requested_delivery_date = line.requested_delivery_date
            date_confirm = line.order_id.date_confirm and datetime.datetime.strptime(line.order_id.date_confirm, '%Y-%m-%d')
            timedelta_until_delivery = datetime.datetime.strptime(requested_delivery_date, '%Y-%m-%d') - ( date_confirm or today )
            return timedelta_until_delivery.days
        except:
            return False

    def _fnct_days_until_delivery(self, cr, uid, ids, field_name, arg, context=None):
        context = context or {}
        res = {}
        for line in self.browse(cr, uid, ids, context=context):
            res[line.id] = self._get_single_days_until_delivery(cr, uid, line.id, line.requested_delivery_date, context=context)
        return res

    def _get_single_default_delivery_date(self, cr, uid, id, delay, context=None):
        today = datetime.datetime(year=datetime.datetime.today().year, month=datetime.datetime.today().month, day=datetime.datetime.today().day)
        if delay and not id:
            default_delivery_datetime = datetime.timedelta(days=delay) + today
            return default_delivery_datetime.strftime('%Y-%m-%d')
        try:
            line = self.browse(cr, uid, id, context=context)
            if not delay:
                delay = line.delay
            date_confirm = line.order_id.date_confirm and datetime.datetime.strptime(line.order_id.date_confirm, '%Y-%m-%d')
            default_delivery_datetime = datetime.timedelta(days=delay) + ( date_confirm or today )
            return default_delivery_datetime.strftime('%Y-%m-%d')
        except:
            return False
        
    def _fnct_default_delivery_date(self, cr, uid, ids, field_name, arg, context=None):
        context = context or {}
        res = {}
        for line in self.browse(cr, uid, ids, context=context):
            if line.state == 'confirmed':
                res[line.id] = line.default_delivery_date_when_confirmed
            else:
                res[line.id] = self._get_single_default_delivery_date(cr, uid, line.id, delay=line.delay, context=context)
        return res

    def onchange_requested_delivery_date(self, cr, uid, ids, requested_delivery_date, default_delivery_date, context=None):
        if not context:
            context = {}
        if not isinstance(ids, list):
            ids = [ids]
        res = {}
        res = {'value':{}}
        res['value']['days_until_delivery'] = self._get_single_days_until_delivery(cr, uid, ids and ids[0], requested_delivery_date=requested_delivery_date, context=None)
        if requested_delivery_date < default_delivery_date:
            res['warning'] = {'title':'Requested days until delivery is less than delivery lead time', 'message':'Please ensure this delivery date is manageable before continuing.'}
        return res

    def button_confirm(self, cr, uid, ids, context=None):
        if not context:
            context = {}
        for line in self.browse(cr, uid, ids, context=context):
            self.write(cr, uid, line.id, {'default_delivery_date_when_confirmed': line.default_delivery_date})
            if line.requested_delivery_date:
                self.write(cr, uid, line.id, {'delay': line.days_until_delivery})
        res = super(sale_order_line, self).button_confirm(cr, uid, ids, context=context)
        return res

    _columns = { 
        'days_until_delivery': fields.function(_fnct_days_until_delivery, string='Days Until Delivery', type='float', help="Number of days remaining until requested delivery date.", readonly=True),
        'requested_delivery_date': fields.date('Requested Delivery Date', select=True, help="Date on which customer has requested delivery."),
        'default_delivery_date_when_confirmed': fields.date('Default Delivery Date When Confirmed'),
        'default_delivery_date': fields.function(_fnct_default_delivery_date, string='Default Delivery Date', type='date', help="Date on which delivery is projected, assuming customer has not requested a specific date."),
    }
    #_defaults = {
    #    'requested_delivery_date': False,
    #}

sale_order_line()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
