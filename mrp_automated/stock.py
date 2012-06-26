## -*- encoding: utf-8 -*-
###############################################################################
##
##    OpenERP, Open Source Management Solution
##    Copyright (C) 2011 credativ ltd (<http://www.credativ.co.uk>). All Rights Reserved
##
##    This program is free software: you can redistribute it and/or modify
##    it under the terms of the GNU General Public License as published by
##    the Free Software Foundation, either version 3 of the License, or
##    (at your option) any later version.
##
##    This program is distributed in the hope that it will be useful,
##    but WITHOUT ANY WARRANTY; without even the implied warranty of
##    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
##    GNU General Public License for more details.
##
##    You should have received a copy of the GNU General Public License
##    along with this program.  If not, see <http://www.gnu.org/licenses/>.
##
###############################################################################

from osv import fields, osv
import netsvc
import datetime

class stock_move(osv.osv):
    
    _inherit = "stock.move"

    def check_prodlot_field(self, cr, uid, ids, context):
        # If the prodlot field is empty open the new prodlot wizard
        for stock_move in self.pool.get('stock.move').browse(cr, uid, ids):
            if stock_move.prodlot_id:
                raise osv.except_osv('No Action Taken','There is already a production lot assigned')
                return False
            else:
                return {
                    'name':("New Production Lot"),
                    'view_mode': 'form',
                    'view_id': False,
                    'view_type': 'form',
                    'res_model': 'wiz.new.prodlot',
                    'res_id': False,
                    'type': 'ir.actions.act_window',
                    'nodestroy': True,
                    'target': 'new',
                    'domain': '[]',
                    'context': dict(context, active_ids=ids)
                }

    def new_prod_lot(self, cr, uid, ids, context):
        # add's a new production lot to a stock move
        move_obj = self.pool.get('stock.move')
        for move in move_obj.browse(cr, uid, ids):
            if not move.prodlot_id:
                prodlot_obj = self.pool.get('stock.production.lot')
                seq_obj = self.pool.get('ir.sequence')
                if context['prodlot_name'] == False:
                    prodlot_name = seq_obj.get(cr,uid, 'stock.lot.serial')
                else:
                    prodlot_name = context['prodlot_name']
                prodlot_id = prodlot_obj.create(cr, uid, {
                    'product_id': move.product_id.id,
                    'name': prodlot_name
                    })
                move_obj.write(cr, uid, move.id, {'prodlot_id':prodlot_id}, context)
            else:
                raise osv.except_osv('No Action Taken', 'The production lot is already assigned')
        return True

    def fifo(self, cr, uid, ids, context):
        # assigns the oldest available production lot if one is available
        move_obj = self.pool.get('stock.move')
        move_item = move_obj.browse(cr,uid,ids[0]) # for the sake of convention I should really do this with a loop
        if not move_item.prodlot_id.id:
            prodlot_obj = self.pool.get('stock.production.lot')
            prodlots = prodlot_obj.search(cr, uid, [('product_id','=',move_item.product_id.id),('stock_available','>',0)], order = 'create_date')
            if prodlots:
                available_stock = 0
                for prodlot in prodlots:
                    if prodlot_obj._get_stock(cr, uid, prodlot, prodlot, context)[prodlot] > move_item.product_qty:
                        move_obj.write(cr, uid, move_item.id, {'prodlot_id': prodlot}, context)
                        return True
                    else:
                        available_stock += prodlot_obj._get_stock(cr, uid, prodlot, prodlot, context)[prodlot]
                if available_stock > move_item.product_qty:
                    raise osv.except_osv('Split Required','There are enough production lots available but the stock move will need to be split')
                    return False
                else:
                    raise osv.except_osv('Not Enough Stock','There is only %s in production lots assign to:\n%s' % (available_stock, move_item.product_id.name))
                    return False
            else:
                raise osv.except_osv('No Production Lots', 'There are no production lots available for:\n%s' % move_item.product_id.name)
                return False
        else:
            raise osv.except_osv('No Action Taken', 'The production lot is already assigned')
            return False

stock_move()
