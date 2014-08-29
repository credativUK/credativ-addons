# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2014 credativ Ltd (<http://credativ.co.uk>).
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

class ResPartner(osv.Model):
    _inherit = 'res.partner'

    def _link_emails_to_partners(self, cr, uid, context=None):
        """Find all emails with no partner_id set and attempt to link them to a partner"""

        lead_sql = """
            UPDATE mail_message mail SET partner_id = lead.partner_id
            FROM crm_lead lead
            WHERE mail.partner_id IS NULL
            AND lead.partner_id IS NOT NULL
            AND mail.model = 'crm.lead'
            AND mail.res_id = lead.id"""

        claim_sql = """
            UPDATE mail_message mail SET partner_id = claim.partner_id
            FROM crm_claim claim
            WHERE mail.partner_id IS NULL
            AND claim.partner_id IS NOT NULL
            AND mail.model = 'crm.claim'
            AND mail.res_id = claim.id"""

        for query in (lead_sql, claim_sql):
            cr.execute(query)

        return True

class CrmPhonecall(osv.Model):
    _inherit = 'crm.phonecall'
    _order = 'date desc'

class CrmMeeting(osv.Model):
    _inherit = 'crm.meeting'
    _order = 'date desc'
