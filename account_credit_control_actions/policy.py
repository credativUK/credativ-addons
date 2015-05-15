# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright 2015 credativ Ltd
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

from openerp.osv import fields, osv

class CreditControlPolicyLevel(osv.osv):
    _inherit = "credit.control.policy.level"

    _columns = {
        'channel': fields.selection([('letter', 'Letter'),
                                   ('email', 'Email'),
                                   ('action', 'Server Action')],
                                  'Channel', required=True),
        'email_template_id': fields.many2one('email.template', 'Email Template', required=False),
        'custom_text': fields.text('Custom Message', translate=True, required=False),
        'server_action_id': fields.many2one('ir.actions.server', 'Server Action', required=False),
    }

    _sql_constraints = [
        ('check_fields_action', "CHECK ((channel='action' AND server_action_id IS NOT NULL) OR channel!='action')",  'The Server Action field is required with this channel'),
        ('check_fields_noaction', "CHECK ((channel!='action' AND email_template_id IS NOT NULL AND custom_text IS NOT NULL) OR channel='action')",  'The Email Template and Custom Message fields are required with this channel'),
    ]
