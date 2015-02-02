# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution   
#    Copyright (C) 2015 credativ ltd (<http://www.credativ.co.uk>). All Rights Reserved
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

import time
from osv import osv, fields
import datetime

class crm_meeting(osv.osv):
    _inherit = "crm.meeting"

    def read_group(self, cr, uid, domain, fields, groupby, offset=0, limit=None, context=None, orderby=False):
        if not context:
            context = {}
        context.update({'virtual_id': False})
        # FIXME: We need to get past an exception in the super class, so we skip all super classes and go straight to the base class - this is ugly!
        res = osv.osv.read_group(self, cr, uid, domain, fields, groupby, offset=offset, limit=limit, context=context, orderby=orderby)
        for re in res:
            re.get('__context', {}).update({'virtual_id' : False})
        return res

    def _get_group_dates(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for line in self.browse(cr, uid, ids, context=context):
            date = datetime.datetime.strptime(line.date, '%Y-%m-%d %H:%M:%S')
            if field_name == 'date_day':
                val = date.strftime('%Y-%m-%d')
            elif field_name == 'date_week':
                iso = date.isocalendar()
                year, week = iso[0], iso[1]-1 # Week is off by one between Python datetime function and ISO calendar
                date_week_start = datetime.datetime.strptime('%s-%s-1' % (year, week), '%Y-%W-%w')
                val = "Week of %s" % (date_week_start.strftime('%Y-%m-%d'))
            res[line.id] = val
        return res

    _columns = {
        'date_day': fields.function(_get_group_dates, string='Date (Day)', type='char', size=10,
                                    store={'crm.meeting': (lambda self, cr, uid, ids, c=None: ids, [], 20)}),
        'date_week': fields.function(_get_group_dates, string='Date (Week)', type='char', size=20,
                                    store={'crm.meeting': (lambda self, cr, uid, ids, c=None: ids, [], 20)}),
        }

crm_meeting()

class crm_phonecall(osv.osv):
    _inherit = "crm.phonecall"

    def _get_group_dates(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for line in self.browse(cr, uid, ids, context=context):
            date = datetime.datetime.strptime(line.date, '%Y-%m-%d %H:%M:%S')
            if field_name == 'date_day':
                val = date.strftime('%Y-%m-%d')
            elif field_name == 'date_week':
                iso = date.isocalendar()
                year, week = iso[0], iso[1]-1 # Week is off by one between Python datetime function and ISO calendar
                date_week_start = datetime.datetime.strptime('%s-%s-1' % (year, week), '%Y-%W-%w')
                val = "Week of %s" % (date_week_start.strftime('%Y-%m-%d'))
            res[line.id] = val
        return res

    _columns = {
        'date_day': fields.function(_get_group_dates, string='Date (Day)', type='char', size=10,
                                    store={'crm.meeting': (lambda self, cr, uid, ids, c=None: ids, [], 20)}),
        'date_week': fields.function(_get_group_dates, string='Date (Week)', type='char', size=20,
                                    store={'crm.meeting': (lambda self, cr, uid, ids, c=None: ids, [], 20)}),
        }

crm_phonecall()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
