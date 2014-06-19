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

import time
from osv import osv, fields
import tools
from datetime import datetime

class CrmLead(osv.osv):
    _inherit = "crm.lead"

    def _get_last_phonecall(self, cr, uid, ids, field_names, args, context=None):
        res = {}

        if not ids:
            return res

        cr.execute("""
            SELECT cl1.id, cp1.id, cp1.date, DATE_PART('days', NOW() - cp1.date)
            FROM crm_lead cl1
            LEFT OUTER JOIN (SELECT cp2.opportunity_id opp_id, MAX(cp2.date) date
                            FROM crm_phonecall cp2
                            GROUP BY cp2.opportunity_id) l2c ON l2c.opp_id = cl1.id
            LEFT OUTER JOIN crm_phonecall cp1 ON l2c.date = cp1.date AND cp1.opportunity_id = cl1.id
            WHERE cl1.id IN (%s);""" % (",".join(str(id) for id in ids)))

        for lead_id, phonecall_id, phonecall_date, phonecall_days in cr.fetchall():
            if 'last_phonecall_id' in field_names:
                res[res[lead]]['last_phonecall_id'] = phonecall_id
            if 'date_last_phonecall' in field_names:
                res[res[lead]]['date_last_phonecall'] = phonecall_date
            if 'days_last_phonecall' in field_names:
                res[res[lead]]['days_last_phonecall'] = phonecall_days
        return res

    def _date_last_search(self, cr, uid, obj, name, args, context):
        ids = set()
        for cond in args:
            amount = cond[2]
            if isinstance(cond[2],(list,tuple)):
                if cond[1] in ['in','not in']:
                    amount = tuple(cond[2])
                else:
                    continue
            else:
                if cond[1] in ['=like', 'like', 'not like', 'ilike', 'not ilike', 'in', 'not in', 'child_of']:
                    continue
                if cond[2] == False:
                    if cond[1] == '=':
                        cond = (cond[0], 'IS', 'NULL')
                        amount = None
                    if cond[1] == '!=':
                        cond = (cond[0], 'IS NOT', 'NULL')
                        amount = None
            query = """SELECT cl1.id FROM crm_lead cl1
            LEFT OUTER JOIN (SELECT cp2.opportunity_id opp_id, MAX(cp2.date) date
                            FROM crm_phonecall cp2
                            GROUP BY cp2.opportunity_id) l2c ON l2c.opp_id = cl1.id
            LEFT OUTER JOIN crm_phonecall cp1 ON l2c.date = cp1.date AND cp1.opportunity_id = cl1.id """

            if name == 'date_last_phonecall':
                where = " WHERE cp1.date %s %%s" % (cond[1],)
            if name == 'days_last_phonecall':
                where = " WHERE DATE_PART('days', NOW() - cp1.date) %s %%s" % (cond[1],)
            cr.execute("%s %s" % (query, where),(amount,))
            res_ids = set(id[0] for id in cr.fetchall())
            ids = ids and (ids & res_ids) or res_ids
        if ids:
            return [('id', 'in', tuple(ids))]
        return [('id', '=', '0')]

    _columns = {
        'last_phonecall_id': fields.function(_get_last_phonecall, multi='last_phonecall_id', type='many2one', relation='crm.phonecall', string='Last Call', help='The last phone call made or scheduled to be made for the lead.'),
        'date_last_phonecall': fields.function(_get_last_phonecall, multi='last_phonecall_id', fnct_search=_date_last_search, type='date', string='Last Call Date', help='The date of the last phone call made or scheduled to be made for the lead.'),
        'days_last_phonecall': fields.function(_get_last_phonecall, multi='last_phonecall_id', fnct_search=_date_last_search, type='integer', string='Days Since Call', help='The days since the last phone call made or scheduled to be made for the lead. This will be negative for a future date.'),
    }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: