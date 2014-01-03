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
from base_deferred_actions.deferred_action import defer_action_quiet
import traceback
import datetime
import netsvc
import psycopg2

class stock_dispatch(osv.osv):
    _inherit = 'stock.dispatch'

    def _get_deferred_state(self, cr, uid, ids, fields, arg, context=None):
        res = {}
        defact_obj = self.pool.get('deferred.action')
        for id in ids:
            pend_ids = defact_obj.search(cr, uid, [('model', '=', 'stock.dispatch'), ('res_id', '=', id), ('state', '=', 'pending'), ('function', '=', 'complete_dispatch')], context=context)
            if pend_ids:
                running = defact_obj.read(cr, uid, pend_ids[0], ['running',], context=context)['running']
                res[id] = running and 'running' or 'queue'
            else:
                res[id] = 'draft'
        return res

    _columns = {
            'state': fields.selection([('draft', 'Draft'), ('waiting', 'Waiting Another Move'), ('confirmed', 'Confirmed'), ('assigned', 'Available'), ('done', 'Done'), ('partial', 'Partial'), ('cancel', 'Cancelled')], 'Status', readonly=True, select=True),
            'deferred_state': fields.function(_get_deferred_state, type='selection', string='Deferred', method=True,
                                selection= [('draft', ''), ('queue', 'Queued for Finalisation'), ('running', 'Finalisation in Progress')],),
        }

    def action_partial(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'partial',}, context=context)
        return True

    def action_done(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'done', 'complete_date': datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'), 'complete_uid': uid})
        return True

    def _get_dispatch_errors(self, cr, uid, id, context=None):
        dispatch = self.browse(cr, uid, id, context=None)
        res = []

        if dispatch.state not in ('confirmed', 'partial'):
            error_str = "Dispatch %s in state %s cannot be completed." % (dispatch.name, dispatch.state,)
            res.append(error_str)

        return res

    def cancel_defer(self, cr, uid, ids, context=None):
        defact_obj = self.pool.get('deferred.action')
        for id in ids:
            pend_ids = defact_obj.search(cr, uid, [('model', '=', 'stock.dispatch'), ('res_id', '=', id), ('state', '=', 'pending'), ('function', '=', 'complete_dispatch')], context=context)
            if pend_ids:
                try:
                    defact_obj.cancel(cr, uid, pend_ids, context=context)
                except osv.except_osv:
                    raise osv.except_osv('Error!', "Dispatch finalisation cannot be cancelled at this point, it may have already started or be complete. Please contact support.")
            else:
                raise osv.except_osv('Error!', "Dispatch finalisation cannot be cancelled at this point, it may have already started or be complete. Please contact support.")
        return True

    @defer_action_quiet
    def complete_dispatch(self, cr, uid, ids, context=None):
        if context is None:
            context = {}

        move_obj = self.pool.get('stock.move')
        wkf_service = netsvc.LocalService('workflow')

        all_messages = []

        for dispatch in self.browse(cr, uid, ids):
            context['from_dispatch'] = dispatch.id
            errors = {}

            errs = self._get_dispatch_errors(cr, uid, dispatch.id, context=context)
            if errs:
                all_messages.extend(errs)
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
                    if move.picking_id and self.test_finished(cr, uid, [move.picking_id.id]):
                        wkf_service.trg_validate(uid, 'stock.picking', move.picking_id.id, 'button_done', cr)
                    else:
                        wkf_service.trg_write(uid, 'stock.picking', move.picking_id.id, cr)
                except psycopg2.OperationalError, e:
                    if e.pgcode in (psycopg2.errorcodes.LOCK_NOT_AVAILABLE, psycopg2.errorcodes.SERIALIZATION_FAILURE, psycopg2.errorcodes.DEADLOCK_DETECTED):
                        raise
                    else:
                        cr.execute("ROLLBACK TO pre_move_done")
                        errors[move] = "Exception: %s\n%s" % (e.__repr__(), traceback.format_exc())
                        continue
                except Exception, e:
                    cr.execute("ROLLBACK TO pre_move_done")
                    errors[move] = "Exception: %s\n%s" % (e.__repr__(), traceback.format_exc())
                    continue

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
