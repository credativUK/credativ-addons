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
from openerp.tools.translate import _

class CreditCommunication(osv.osv_memory):
    _inherit = "credit.control.communication"

    def _generate_actions(self, cr, uid, comms, context=None):
        """Run server action using server action ID related to level"""
        if context == None:
            context = {}
        cr_line_obj = self.pool.get('credit.control.line')
        server_action_obj = self.pool.get('ir.actions.server')

        for comm in comms:
            if not comm.current_policy_level.server_action_id:
                raise osv.except_osv(_('Error !'), _("Credit control line is set to server action but no server action set for policy level"))

            action = comm.current_policy_level.server_action_id
            res_id = False
            if action.model_id.model == 'res.partner':
                res_id = comm.partner_id.id
            elif action.model_id.model == 'credit.control.communication':
                res_id = comm.id
            else:
                raise osv.except_osv(_('Error !'), _("The policy level server action should be for a Partner or Credit Control Communication"))

            ctx = context.copy()
            ctx.update({
                    'active_id': res_id,
                    'active_model': action.model_id.model,
            })
            server_action_obj.run(cr, uid, [action.id], ctx)

        self._mark_credit_line_as_sent(cr, uid, comms, context=context)
        return True
