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

class crm_calls_wizard(osv.osv_memory):
    _name = "crm.calls.wizard"
    _inherit = 'crm.phonecall2phonecall'
    _description = "Schedule Calls"

    _columns = {
        'action': fields.selection([('schedule','Schedule a call'), ('log','Log a call')], 'Action', required=False),
    }

    def default_get(self, cr, uid, fields, context=None):
        opp_obj = self.pool.get('crm.lead')
        categ_id = False
        data_obj = self.pool.get('ir.model.data')
        res_id = data_obj._get_id(cr, uid, 'crm', 'categ_phone2')
        if res_id:
            categ_id = data_obj.browse(cr, uid, res_id, context=context).res_id

        record_ids = context and context.get('active_ids', []) or []
        res = {}
        res.update({'date': time.strftime('%Y-%m-%d %H:%M:%S')})
        for opp in opp_obj.browse(cr, uid, record_ids, context=context):
            if 'user_id' in fields:
                res.update({'user_id': opp.user_id and opp.user_id.id or False})
            if 'section_id' in fields:
                res.update({'section_id': opp.section_id and opp.section_id.id or False})
            if 'categ_id' in fields:
                res.update({'categ_id': categ_id})
        return res

    def action_schedule(self, cr, uid, ids, context=None):
        value = {}
        if context is None:
            context = {}
        phonecall = self.pool.get('crm.phonecall')
        opportunity_ids = context and context.get('active_ids') or []
        opportunity = self.pool.get('crm.lead')
        data = self.browse(cr, uid, ids, context=context)[0]
        call_ids = []
        for opportunity_id in opportunity.browse(cr, uid, opportunity_ids, context=context):
            call_id = opportunity.schedule_phonecall(cr, uid, [opportunity_id.id,], data.date, data.name,
                    data.note, opportunity_id.phone or (opportunity_id.partner_address_id and opportunity_id.partner_address_id.phone or False),
                    opportunity_id.partner_address_id and opportunity_id.partner_address_id.name or False,
                    data.user_id and data.user_id.id or False,
                    data.section_id and data.section_id.id or False,
                    data.categ_id and data.categ_id.id or False,
                    action='schedule', context=context)
            call_ids.append(call_id)
        return {'type': 'ir.actions.act_window_close'}

crm_calls_wizard()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
