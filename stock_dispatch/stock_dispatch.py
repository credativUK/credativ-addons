# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2011 credativ Ltd (<http://credativ.co.uk>).
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
import time
from osv.orm import except_orm
from tools.translate import _
import netsvc

class stock_dispatch(osv.osv):
    _name = 'stock.dispatch'
    _description = 'Stock Dispatch'
    _rec_name = 'id'
    _columns = {
        'stock_moves': fields.one2many('stock.move', 'dispatch_id', 'Stock Moves', required=True, select=True,
                        domain=[('state', '=', 'assigned'), ('picking_type', '=', 'out')], readonly=True, states={'draft':[('readonly',False)]}),
        'carrier_id': fields.many2one('res.partner', 'Carrier', required=True, select=True, readonly=True, states={'draft':[('readonly',False)]}),
        'complete_uid': fields.many2one('res.users', 'Completed User', readonly=True),
        'complete_date': fields.datetime('Completed date', readonly=True),
        'date': fields.datetime('Date created', readonly=True),
        'state': fields.selection([('draft', 'Draft'), ('confirmed', 'Confirmed'), ('done', 'Done'), ('cancel', 'Cancelled')], 'Status', readonly=True, select=True),
        'dispatch_date': fields.date('Planned Dispatch Date', required=True, readonly=True, states={'draft':[('readonly',False)]}),
        }

    _order = 'id desc'

    _defaults = {
        'state': lambda *a: 'draft',
        'date': lambda *a: time.strftime('%Y-%m-%d %H:%M:%S'),
        'dispatch_date': lambda *a: time.strftime('%Y-%m-%d'),
    }

    def name_get(self, cr, uid, ids, context={}):
        return [(i, str(i)) for i in ids]

    def on_change_stock_moves(self, cr, uid, id, stock_moves, context=None):
        move_list = []
        move_string = ''
        warning = False
        if stock_moves[0][2]:
            for move in self.pool.get('stock.move').browse(cr, uid, stock_moves[0][2]):
                if move.dispatch_id and move.dispatch_id.id != id[0]:
                    warning = True
                    move_string += ' (id:%d,dispatch_id:%d)' % (move.id, move.dispatch_id.id)
                else: move_list.append(move.id)
            result = {'value': {'stock_moves': move_list}}
            if warning:
                result['warning'] = {'title': 'Cannot add all stock moves',
                                     'message': 'One or more moves are already part of another dispatch and' \
                                     ' have not been added:%s' % (move_string)}
            if sorted(stock_moves[0][2]) == sorted(move_list):
              return {} # Prevent update when there is no actual change
            return result
        return {}

    def test_finished(self, cr, uid, picking_ids):
        # this is similar to stock.picking.test_finnished - but that
        # has a bug in it which we might hit - https://bugs.launchpad.net/openobject-addons/+bug/690583
        move_ids = self.pool.get('stock.move').search(cr, uid, [('picking_id', 'in', picking_ids)])
        for move in self.pool.get('stock.move').browse(cr, uid, move_ids):
            if move.state not in ('done', 'cancel'):
                return False
        return True

    def action_done(self, cr, uid, ids, context=None):
        if context is None:
            context = {}

        for dispatch in self.browse(cr, uid, ids):
            context['from_dispatch'] = dispatch.id
            picking_obj = self.pool.get('stock.picking')
            move_ids = [x.id for x in dispatch.stock_moves]
            self.pool.get('stock.move').action_done(cr, uid, move_ids, context=context)
            
            wkf_service = netsvc.LocalService('workflow')
            for move in self.pool.get('stock.move').browse(cr, uid, move_ids, context):
                if move.picking_id and self.test_finished(cr, uid, [move.picking_id.id]):
                    wkf_service.trg_validate(uid, 'stock.picking', move.picking_id.id, 'button_done', cr)
                else:
                    # cause workflow to update since we called move.action_done
                    wkf_service.trg_write(uid, 'stock.picking', move.picking_id.id, cr)

        self.write(cr, uid, ids, {'state': 'done', 'complete_date': time.strftime('%Y-%m-%d %H:%M:%S'), 'complete_uid': uid})
        return True

    def action_cancel(self, cr, uid, ids, context=None):
        if context is None:
            context = {}

        for dispatch in self.browse(cr, uid, ids):
            move_ids = [x.id for x in dispatch.stock_moves]
            self.pool.get('stock.move').write(cr, uid, move_ids, {'dispatch_id': False})
        self.write(cr, uid, ids, {'state': 'cancel'})
        return True

    def unlink(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        ctx = context.copy()
        for dispatch in self.browse(cr, uid, ids, context=ctx):
            if dispatch.state != 'draft' and not ctx.get('call_unlink',False):
                raise osv.except_osv(_('UserError'),
                        _('You can only delete draft dispatches.'))
        return super(stock_dispatch, self).unlink(
            cr, uid, ids, context=ctx)


stock_dispatch()
