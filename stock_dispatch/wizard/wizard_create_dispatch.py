# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution   
#    Copyright (C) 2011 credativ Ltd (<http://credativ.co.uk>).
#    All Rights Reserved
#    $Id$
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

import netsvc
import time
from osv import osv, fields
from tools.translate import _

class stock_move_create_dispatch(osv.osv_memory):
    _name = "stock.move.create_dispatch"
    _description = "Create Dispatch"
    _columns = {
        'move_ids' : fields.text('Stock Moves', required=True), # Store an array of IDs instead of having to make complex osv_memory tables for one2many
        'carrier_id' : fields.many2one('res.partner', 'Carrier', required=True),
        'dispatch_date': fields.date('Planned Dispatch Date', required=True),
    }
    _defaults = {
        'dispatch_date': lambda *a: time.strftime('%Y-%m-%d'),
    }

    def default_get(self, cr, uid, fields, context):
        move_ids = context and context.get('active_ids', False) or False
        self._check_moves(cr,uid, move_ids, context)
        res = super(stock_move_create_dispatch, self).default_get(cr, uid, fields, context=context)
        res.update({'move_ids': ','.join((str(x) for x in move_ids)) or False})
        return res
    
    def _check_moves(self, cr, uid, move_ids, context):
        move_string = ''
        error = False
        
        for move in self.pool.get('stock.move').browse(cr, uid, move_ids):
            if move.dispatch_id:
                error = True
                move_string += ' (id:%d,dispatch_id:%d)' % (move.id, move.dispatch_id.id)
        
        if error:
            raise osv.except_osv(_('UserError'), _('One or more moves are already part of another dispatch and' \
                                ' can not been added to a new one:%s' % (move_string)))

    def create_dispatch(self, cr, uid, ids, context=None):
        rec_id = context and context.get('active_id', False)
        assert rec_id, _('Active ID is not set in Context')

        dispatch_obj = self.pool.get('stock.dispatch')

        for data in self.browse(cr, uid, ids, context=context):
            move_ids = [int(x) for x in data.move_ids.split(',')]
            self._check_moves(cr,uid, move_ids, context)
            dispatch_data = {
                        'carrier_id': data.carrier_id.id,
                        'dispatch_date': data.dispatch_date,
                        'stock_moves': ([6, 0, move_ids],),
                }
            dispatch = dispatch_obj.create(cr, uid, dispatch_data)

        return {
                'name': 'Dispatch',
                'view_type': 'form',
                'view_mode': 'form,tree',
                'res_model': 'stock.dispatch',
                'view_id': False,
                'res_id': dispatch,
                'type': 'ir.actions.act_window',
            }

stock_move_create_dispatch()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

