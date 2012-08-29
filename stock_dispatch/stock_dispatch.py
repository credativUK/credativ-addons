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
import datetime, time
from osv.orm import except_orm
from tools.translate import _
import netsvc
import pytz
import tools

class stock_dispatch(osv.osv):
    _name = 'stock.dispatch'
    _description = 'Stock Dispatch'
    
    _columns = {
        'name' : fields.char('Name', size=128, required=True, readonly=True, states={'draft': [('readonly', False)]}, select=True),
        'stock_moves': fields.one2many('stock.move', 'dispatch_id', 'Stock Moves', select=True, readonly=True, states={'draft':[('readonly',False)]}),
        'carrier_id': fields.many2one('res.partner', 'Carrier', required=True, select=True, readonly=True, states={'draft':[('readonly',False)]}),
        'complete_uid': fields.many2one('res.users', 'Completed User', readonly=True),
        'complete_date': fields.datetime('Completed date', readonly=True),
        'date': fields.datetime('Date created', readonly=True),
        'state': fields.selection([('draft', 'Draft'), ('waiting', 'Waiting Another Move'), ('confirmed', 'Confirmed'), ('assigned', 'Available'), ('done', 'Done'), ('cancel', 'Cancelled')], 'Status', readonly=True, select=True),
        'dispatch_date': fields.date('Planned Dispatch Date', required=True, readonly=True, states={'draft':[('readonly',False)]}),
        'cutoff_date': fields.datetime('Cutoff Date', required=True, readonly=True, states={'draft':[('readonly',False)]}),
        }

    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'Dispatch Name must be unique !'),
        ('cutoff_before_dispatch', 'CHECK (cutoff_before_dispatch<dispatch_date)',  'The cutoff date must occur before the dispatch'),
    ]

    _order = 'name desc'

    _defaults = {
        'name': lambda obj, cr, uid, context: obj.pool.get('ir.sequence').get(cr, uid, 'stock.dispatch'),
        'state': lambda *a: 'draft',
        'date': lambda *a: datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
        'dispatch_date': lambda *a: datetime.datetime.utcnow().strftime('%Y-%m-%d'),
    }

    def on_change_dispatch_date(self, cr, uid, id, dispatch_date, context=None):
        res = {'value': {}}
        if dispatch_date:
            tz = self.pool.get('res.users').read(cr, uid, uid, ['context_tz'])['context_tz']
            cutoff = (datetime.datetime.strptime(dispatch_date, '%Y-%m-%d') - datetime.timedelta(days=1)).replace(hour=15, minute=0, second=0)
            # FIXME: DST not working correctly in OpenERP - no idea why it is failing, but I have resorted to hard coding European DST date ranges to get the default value
            if tz == 'GMT':
                dst_start = 31 - ((((5 * cutoff.year) / 4) + 4) % 7)
                dst_end = 31 - ((((5 * cutoff.year) / 4) + 1) % 7)
                if ((cutoff.month == 3 and cutoff.day >= dst_start) or
                   (cutoff.month > 3 and cutoff.month < 10) or
                   (cutoff.month == 10 and cutoff.day <= dst_end)):
                    cutoff = cutoff.replace(hour=14)
            # FIXME: End
            cutoff = cutoff.strftime('%Y-%m-%d %H:%M:%S')
            res['value']['cutoff_date'] = tools.server_to_local_timestamp(cutoff, '%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M:%S', tz)
        return res
        
    def on_change_stock_moves(self, cr, uid, ids, stock_moves, context=None):
        move_list = []
        move_string = ''
        warning = False
        if stock_moves[0][2]:
            for move in self.pool.get('stock.move').browse(cr, uid, stock_moves[0][2]):
                if move.dispatch_id and move.dispatch_id.id != ids[0]:
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
            move_ids = [x.id for x in dispatch.stock_moves]
            self.pool.get('stock.move').action_done(cr, uid, move_ids, context=context)
            
            wkf_service = netsvc.LocalService('workflow')
            for move in self.pool.get('stock.move').browse(cr, uid, move_ids, context):
                if move.picking_id and self.test_finished(cr, uid, [move.picking_id.id]):
                    wkf_service.trg_validate(uid, 'stock.picking', move.picking_id.id, 'button_done', cr)
                else:
                    # cause workflow to update since we called move.action_done
                    wkf_service.trg_write(uid, 'stock.picking', move.picking_id.id, cr)

        self.write(cr, uid, ids, {'state': 'done', 'complete_date': datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'), 'complete_uid': uid})
        return True

    def action_cancel(self, cr, uid, ids, context=None):
        if context is None:
            context = {}

        for dispatch in self.browse(cr, uid, ids):
            move_ids = [x.id for x in dispatch.stock_moves]
            self.pool.get('stock.move').write(cr, uid, move_ids, {'dispatch_id': False})
        self.write(cr, uid, ids, {'state': 'cancel'})
        return True

    def action_draft(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'draft'})
        return True

    def action_confirm(self, cr, uid, ids, context=None):
        for dispatch in self.browse(cr, uid, ids):
            move_ids = [x.id for x in dispatch.stock_moves]
            if len(move_ids) == 0:
                raise osv.except_osv('Could not confirm dispatch',
                      'A dispatch must have atleast one stock move assigned to it')
        self.write(cr, uid, ids, {'state': 'confirmed'})
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

    def copy_data(self, cr, uid, id, default=None, context=None):
        if not default:
            default = {}
        default['stock_moves'] = []
        return super(stock_dispatch, self).copy_data(cr, uid, id, default, context)

stock_dispatch()
