# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 credativ Ltd (<http://credativ.co.uk>).
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

from osv import osv

class crm_lead_launch_map(osv.osv):
    _inherit = "crm.lead"

    def open_map(self, cr, uid, ids, context=None):
        lead_obj = self.pool.get('crm.lead')
        lead = lead_obj.browse(cr, uid, ids, context=context)[0]
        url="http://maps.google.com/maps?oi=map&q="
        if lead.street:
            url+=lead.street.replace(' ','+')
        if lead.city:
            url+='+'+lead.city.replace(' ','+')
        if lead.state_id:
            url+='+'+lead.state_id.name.replace(' ','+')
        if lead.country_id:
            url+='+'+lead.country_id.name.replace(' ','+')
        if lead.zip:
            url+='+'+lead.zip.replace(' ','+')
        return {
        'type': 'ir.actions.act_url',
        'url':url,
        'target': 'new'
        }

crm_lead_launch_map()

class crm_meeting_launch_map(osv.osv):
    _inherit = "crm.meeting"

    def open_map(self, cr, uid, ids, context=None):
        meeting_obj = self.pool.get('crm.meeting')
        meeting = meeting_obj.browse(cr, uid, ids, context=context)[0]
        if not meeting.partner_address_id:
            return False
        url="http://maps.google.com/maps?oi=map&q="
        if meeting.partner_address_id.street:
            url+=meeting.partner_address_id.street.replace(' ','+')
        if meeting.partner_address_id.city:
            url+='+'+meeting.partner_address_id.city.replace(' ','+')
        if meeting.partner_address_id.state_id:
            url+='+'+meeting.partner_address_id.state_id.name.replace(' ','+')
        if meeting.partner_address_id.country_id:
            url+='+'+meeting.partner_address_id.country_id.name.replace(' ','+')
        if meeting.partner_address_id.zip:
            url+='+'+meeting.partner_address_id.zip.replace(' ','+')
        return {
        'type': 'ir.actions.act_url',
        'url':url,
        'target': 'new'
        }

crm_meeting_launch_map()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

