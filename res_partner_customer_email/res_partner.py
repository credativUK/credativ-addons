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

class res_partner(osv.osv):
    """Inherit res.partner to trigger automatic email upon customer creation.
    """
    _inherit = 'res.partner'

    def create(self, cr, uid, vals, context=None):
        """Send email to newly created customer when they are not opt-out and not duplicated from another
        """
        if context is None:
            context = {}

        res = super(res_partner, self).create(cr, uid, vals, context=context)

        customer = vals.get('customer', False)
        email_address = vals.get('email', False)
        # Do not trigger email when customer created by duplicating another
        customer_created_from_duplication = vals.get('name', False) and vals['name'][-6:] == '(copy)'
        # Do not trigger email when customer set as opt-out
        opt_out = vals.get('opt_out', False)

        if customer and email_address and not customer_created_from_duplication and not opt_out:
            ir_model_data = self.pool.get('ir.model.data')
            action_server_pool = self.pool.get('ir.actions.server')
            server_action_id = ir_model_data.get_object_reference(cr, uid, 'res_partner_customer_email', 'action_new_customer_email')
            ctx = {'active_id':res,'active_ids':[res]}
            if server_action_id:
                action_server_pool.run(cr, uid, [server_action_id[1]], context=ctx)
            else:
                _logger.error("New customer email template not found. Email could not be sent.")

        return res

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
