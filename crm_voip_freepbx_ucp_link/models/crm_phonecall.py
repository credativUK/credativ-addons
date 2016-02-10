# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2016 credativ Ltd (<http://credativ.co.uk>).
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

from openerp import models, api, _
from openerp.exceptions import UserError

from urllib2 import quote
import re

class CrmPhonecall(models.Model):
    _inherit = "crm.phonecall"

    @api.multi
    def freepbx_open_ucp(self):
        self.ensure_one()
        params = self.env['ir.config_parameter']

        base_url = params.get_param('crm.voip.ucp_url', default='http://localhost/ucp')

        my_ext = self.user_id.sip_login or self.user_id.sip_external_phone
        call_ext = self.partner_phone or self.partner_mobile or ''
        if not my_ext:
            raise UserError(_('The salesman assigned to this call has no VOIP extension configured.'))
        if not call_ext:
            raise UserError(_('This call has no number set'))
        call_ext = re.sub(r'[^0-9]', '', call_ext)

        search_url = "%s?display=dashboard&mod=cdr&search=%s&sub=%s" % (base_url, quote(call_ext), quote(my_ext))

        client_action = {'type': 'ir.actions.act_url',
                         'name': "FreePBX UCP",
                         'target': 'new',
                         'url': search_url,
                         }
        return client_action
