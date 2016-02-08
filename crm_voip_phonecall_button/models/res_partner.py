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

from openerp.osv import fields, osv

class res_partner(osv.osv):
    """ Inherits partner and adds CRM phonecalls in the partner form """
    _inherit = 'res.partner'

    # TODO: Convert to new api
    def _phonecalls_count(self, cr, uid, ids, field_name, arg, context=None):
        res = dict(map(lambda x: (x,{'phone_logs_count': 0}), ids))
        # the user may not have access rights for phonecalls
        try:
            for partner in self.browse(cr, uid, ids, context):
                if partner.is_company:
                    operator = 'child_of'
                else:
                    operator = '='
                schedulecall_ids = self.pool['crm.phonecall'].search(cr, uid, [('partner_id', operator, partner.id), ('state', '=', 'open')], context=context)
                res[partner.id] = {
                    'phone_logs_count': len(schedulecall_ids),
                }
        except:
            pass
        return res

    _columns = {
        'phonecalls_count': fields.function(_phonecalls_count, string='PhoneCalls', type='integer'),
    }
