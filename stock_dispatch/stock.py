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
from osv.orm import except_orm
from tools.translate import _

class stock_move(osv.osv):
    _inherit = 'stock.move'
    _columns = {
        'dispatch_id': fields.many2one('stock.dispatch', 'Dispatch'),
        'picking_type': fields.related('picking_id', 'type', type='selection', selection=
                                        [('out', 'Sending Goods'),
                                         ('in', 'Getting Goods'),
                                         ('internal', 'Internal')],
                                        string="Shipping Type", help="Shipping type specify, goods coming in or going out.", store=True, select=True),
        }

    def action_done(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        
        for move in self.browse(cr, uid, ids):
            # Only allow done state if all of the moves are actualy part
            # of this dispatch, or if they are not part of a dispatch and
            # this is not called from the dispatch view
            if move.dispatch_id and move.dispatch_id.id != context.get('from_dispatch', False):
                raise except_orm(_('UserError'),
                        _('This move is part of a dispatch and can only' \
                          ' be completed through the dispatch view: (name: "%s", id: %d, dispatch: %s)') % \
                          (move.name, move.id, move.dispatch_id.name))
        
        return super(stock_move, self).action_done(cr, uid, ids, context)

    def copy_data(self, cr, uid, id, default=None, context=None):
        if not default:
            default = {}
        default['dispatch_id'] = False
        return super(stock_move, self).copy_data(cr, uid, id, default, context)

    def cancel_assign(self, cr, uid, ids, context=None):
        for move in self.browse(cr, uid, ids):
            # Only allow cancel if not in dispatch
            if move.dispatch_id and move.dispatch_id.state in ('done', 'confirmed'):
                raise except_orm(_('UserError'), _('This move is part of a confirmed dispatch and assignment cannot be cancelled: (name: "%s", id: %d, dispatch: %s)') % (move.name, move.id, move.dispatch_id.name))
        self.write(cr, uid, ids, {'dispatch_id': False})
        return super(stock_move, self).cancel_assign(cr, uid, ids, context)

    def action_cancel(self, cr, uid, ids, context=None):
        for move in self.browse(cr, uid, ids):
            # Only allow cancel if not in dispatch
            if move.dispatch_id and move.dispatch_id.state in ('done', 'confirmed'):
                raise except_orm(_('UserError'), _('This move is part of a confirmed dispatch and cannot be cancelled: (name: "%s", id: %d, dispatch: %s)') % (move.name, move.id, move.dispatch_id.name))
        self.write(cr, uid, ids, {'dispatch_id': False})
        return super(stock_move, self).action_cancel(cr, uid, ids, context)

    def action_scrap(self, cr, uid, ids, quantity, location_id, context=None):
        for move in self.browse(cr, uid, ids):
            # Only allow scrap if not in dispatch
            if move.dispatch_id and move.dispatch_id.state in ('done', 'confirmed'):
                raise except_orm(_('UserError'), _('This move is part of a confirmed dispatch and cannot be scapped: (name: "%s", id: %d, dispatch: %s)') % (move.name, move.id, move.dispatch_id.name))
        self.write(cr, uid, ids, {'dispatch_id': False})
        return super(stock_move, self).action_scrap(cr, uid, ids, quantity, location_id, context=context)

    def action_split(self, cr, uid, ids, quantity, split_by_qty=1, prefix=False, with_lot=True, context=None):
        for move in self.browse(cr, uid, ids):
            # Only allow split if not in dispatch
            if move.dispatch_id and move.dispatch_id.state in ('done', 'confirmed'):
                raise except_orm(_('UserError'), _('This move is part of a confirmed dispatch and cannot be split: (name: "%s", id: %d, dispatch: %s)') % (move.name, move.id, move.dispatch_id.name))
        self.write(cr, uid, ids, {'dispatch_id': False})
        return super(stock_move, self).action_split(cr, uid, ids, quantity, split_by_qty=split_by_qty, prefix=prefix, with_lot=with_lot, context=context)

    def do_partial(self, cr, uid, ids, partial_datas, context=None):
        for move in self.browse(cr, uid, ids):
            # Only allow partial if not in dispatch
            if move.dispatch_id and move.dispatch_id.state in ('done', 'confirmed'):
                raise except_orm(_('UserError'), _('This move is part of a confirmed dispatch and cannot be partially picked: (name: "%s", id: %d, dispatch: %s)') % (move.name, move.id, move.dispatch_id.name))
        self.write(cr, uid, ids, {'dispatch_id': False})
        return super(stock_move, self).do_partial(cr, uid, ids, partial_datas, context=context)

    def write(self, cr, uid, ids, vals, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        frozen_fields = set(['product_qty', 'product_uom', 'product_uos_qty', 'product_uos', 'location_id', 'location_dest_id',
                             'product_id', 'name', 'priority', 'address_id', 'prodlot_id', 'price_unit', 'price_currency_id', 'backorder_id'])
        for move in self.browse(cr, uid, ids, context=context):
            if move.dispatch_id and move.dispatch_id.state in ('done', 'confirmed'):
                if frozen_fields.intersection(vals):
                    raise osv.except_osv(_('UserError'),
                                            _('This move is part of a confirmed dispatch and this field cannot be edited: (name: %s, id: %d, dispatch: %s)') % (move.name, move.id, move.dispatch_id.name))
        return super(stock_move, self).write(cr, uid, ids, vals, context=context)

stock_move()
