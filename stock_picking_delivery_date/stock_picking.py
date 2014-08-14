# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2014 credativ Ltd (<http://credativ.co.uk>).
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

from openerp.osv import fields, osv

import stock
import time

class stock_picking_out(osv.osv):
    _inherit='stock.picking.out'

    def create(self, cr, user, vals, context=None):
        
        new_id = super(stock_picking_out, self).create(cr, user, vals, context)
        #Update newly created stock moves 
        sql_str = """update stock_move set
                    date_expected='%s'
                where
                    picking_id=%s """ % (vals['min_date'], new_id)
        cr.execute(sql_str)
        return new_id

    def _set_minimum_date(self, cr, uid, ids, name, value, arg, context=None):
        pick_obj = self.pool.get('stock.picking.out')
        if not value:
            return False

        sql_str = """update stock_picking set
                    min_date='%s'
                where
                    id=%s """ % (value, ids)
        cr.execute(sql_str)
        sql_str = """update stock_move set
                    date_expected='%s'
                where
                    picking_id=%s """ % (value, ids)
        cr.execute(sql_str)
        return True
    
    def get_min_max_date(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for pick in ids:
            res[pick] = {}
            res[pick]['min_date'] = self.pool.get('stock.picking').browse(cr, uid, pick, context=context)['min_date']
            res[pick]['max_date'] = self.pool.get('stock.picking').browse(cr, uid, pick, context=context)['max_date']
        return res
    
    def _set_maximum_date(self, cr, uid, ids, name, value, arg, context=None):
        return True
    
    def _get_stock_move_changes(self, cr, uid, ids, context=None):
        return []

    _columns = {
        'min_date': fields.function(get_min_max_date,fnct_inv=_set_minimum_date,multi='min_max_date',store={
                'stock.move': (
                    _get_stock_move_changes,
                    ['date_expected'], 10,
                    )
                },type='datetime', string='Scheduled Time', select=True,help="Scheduled time for the shipment to be processed"),
        'max_date': fields.function(get_min_max_date,fnct_inv=_set_maximum_date, multi='min_max_date',store={'stock.move': (
                    _get_stock_move_changes,
                    ['date_expected'], 10,
                    )},type='datetime', string='Max. Expected Date', select=True    ),

        
        }

class stock_move(osv.osv):
    _inherit = 'stock.move'
    
    def _default_date_expected(self, cr, uid, context=None):
        if 'date_expected' in context and context['date_expected']:
            return context['date_expected']
        else:
            return time.strftime('%Y-%m-%d %H:%M:%S')
    
    _defaults = {
        'date_expected': _default_date_expected
    }
