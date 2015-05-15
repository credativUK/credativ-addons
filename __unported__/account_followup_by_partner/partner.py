# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2014 credativ Ltd (<http://credativ.co.uk>).
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
from openerp.tools.translate import _

class ResPartner(osv.Model):
    _inherit = 'res.partner'
    _columns = {
        'followup_email': fields.boolean('Email Followups', help='If unchecked, follow up emails will not be sent to this partner.'),
    }

    _defaults = {
        'followup_email': lambda *a: 0,
    }

    def do_partner_mail(self, cr, uid, partner_ids, context=None):
        if context is None:
            context = {}
        partner_len = len(partner_ids)
        if context.get('account_followup_skip_partners'):
            partner_ids = self.search(cr, uid, [('id', 'in', partner_ids), ('followup_email', '=', True)], context=context)
        if self.search(cr, uid, [('id', 'in', partner_ids), ('followup_email', '!=', True)], context=context):
            raise osv.except_osv(_('Error!'),_("The partner is set to not receive followup emails but you are attempting to send one for this partner."))
        res = super(ResPartner, self).do_partner_mail(cr, uid, partner_ids, context=context)
        res += partner_len - len(partner_ids)
        return res
