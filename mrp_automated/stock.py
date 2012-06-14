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

    def new_prod_lot(self, cr, uid, ids, context):
        # add's a new production lot to a stock move
        move_obj = self.pool.get('stock.move')
        move_item = move_obj.browse(cr, uid, ids[0])
        if not move_item.prodlot_id: 
            prodlot_obj = self.pool.get('stock.production.lot')
            seq_obj = self.pool.get('ir.sequence')
            seq_next = seq_obj.get(cr,uid, 'stock.lot.serial')
        
            prodlot_id = prodlot_obj.create(cr, uid, {
                'product_id': move_item.product_id.id,
                'name': seq_next
                })
            move_obj.write(cr, uid, ids[0], {'prodlot_id':prodlot_id}, context)
                      
        return True

    def fifo(self, cr, uid, ids, context):
        # assigns the oldest available production lot if one is available
        move_obj = self.pool.get('stock.move')
        move_item = move_obj.browse(cr,uid,ids[0])
        if not move_item.prodlot_id.id:
            prodlot_obj = self.pool.get('stock.production.lot')
            prodlots = prodlot_obj.search(cr, uid, [('product_id','=',move_item.product_id.id),('stock_available','>',0)], order = 'create_date')
            if prodlots:
                move_obj.write(cr, uid, move_item.id, {'prodlot_id': prodlots[0]}, context)
                return True
            else:
                print 'there are no production lots available for this product, please make one'
                return False
        else:
            #whack in an error message saying that there is already something there, and that the user is a bellend
            print 'the production lot is ', move_item.prodlot_id.id, ':', move_item.prodlot_id.name
            return False
        
        return False

stock_move()
