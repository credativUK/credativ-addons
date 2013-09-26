# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2013 credativ Ltd (<http://credativ.co.uk>).
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

from osv import osv, fields
from osv.orm import except_orm
from base_deferred_actions.deferred_action import defer_action
import traceback
import datetime
import netsvc

class stock_dispatch(osv.osv):
    _inherit = 'stock.dispatch'

    _columns = {
            'state': fields.selection([('draft', 'Draft'), ('waiting', 'Waiting Another Move'), ('confirmed', 'Confirmed'), ('assigned', 'Available'), ('done', 'Done'), ('partial', 'Partial'), ('cancel', 'Cancelled')], 'Status', readonly=True, select=True),
        }

    def action_partial(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'partial',}, context=context)
        return True

    def action_done(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'done', 'complete_date': datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'), 'complete_uid': uid})
        return True

    @defer_action
    def complete_dispatch(self, cr, uid, ids, context=None):
        if context is None:
            context = {}

        move_obj = self.pool.get('stock.move')
        wkf_service = netsvc.LocalService('workflow')
        
        all_messages = []

        for dispatch in self.browse(cr, uid, ids):
            context['from_dispatch'] = dispatch.id
            errors = {}

            if dispatch.state not in ('confirmed', 'partial'):
                error_str = "Dispatch %s in state %s cannot be completed." % (dispatch.name, dispatch.state,)
                all_messages.append(error_str)
                continue

            for move in dispatch.stock_moves:
                if move.state == 'done':
                    continue

                if move.state == 'cancel':
                    errors[move] = "This dispatch contains a cancelled stock move. This may be due to a cancellation during the complete action."
                    continue

                cr.execute("SAVEPOINT pre_move_done")
                try:
                    move_obj.action_done(cr, uid, [move.id,], context=context)
                except Exception, e:
                    cr.execute("ROLLBACK TO pre_move_done")
                    errors[move] = "Exception: %s\n%s" % (e.__repr__(), traceback.format_exc())
                    continue

                if move.picking_id and self.test_finished(cr, uid, [move.picking_id.id]):
                    wkf_service.trg_validate(uid, 'stock.picking', move.picking_id.id, 'button_done', cr)
                else:
                    wkf_service.trg_write(uid, 'stock.picking', move.picking_id.id, cr)

            if errors:
                error_str = "Dispatch %s was partially completed with the following errors:\n" % (dispatch.name,)
                for move, error in errors.iteritems():
                    error_str += "Move: %s\n%s\n" % (move.id, error)
                all_messages.append(error_str)
                wkf_service.trg_validate(uid, 'stock.dispatch', dispatch.id, 'partial', cr)
            else:
                error_str = "Dispatch %s was completed." % (dispatch.name,)
                all_messages.append(error_str)
                wkf_service.trg_validate(uid, 'stock.dispatch', dispatch.id, 'done', cr)

        if not all_messages:
            return "All actions completed successfully"
        else:
            return "\n\n".join(all_messages)

stock_dispatch()
