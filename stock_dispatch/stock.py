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
                          ' be completed through the dispatch view: (name: "%s", id: %d)') % \
                          (move.name, move.id,))
        
        return super(stock_move, self).action_done(cr, uid, ids, context)

    def copy_data(self, cr, uid, id, default=None, context=None):
        if not default:
            default = {}
        default['dispatch_id'] = False
        return super(stock_move, self).copy_data(cr, uid, id, default, context)
        
    def action_cancel(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        for move in self.browse(cr, uid, ids):
            # Do not allow cancel when part of a dispatch.
            if move.dispatch_id:
                raise except_orm(_('UserError'),
                    _('This move is part of a dispatch and must first be removed'
                    ' from the dispatch before cancelling: (name: "%s", id: %d)') %
                (move.name, move.id) )
        return super(stock_move, self).action_cancel(cr, uid, ids, context)

stock_move()
