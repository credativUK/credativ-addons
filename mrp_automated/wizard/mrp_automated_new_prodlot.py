# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2011 credativ ltd (<http://www.credativ.co.uk>). All Rights Reserved
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

from osv import fields, osv

class wiz_new_prodlot(osv.osv_memory):
    _name = 'wiz.new.prodlot'
    _description = 'Add New Production Lot'
    
    _columns = {
        'prodlot_id': fields.char('Production Lot ID', size=64, required=False),
    }

    def add_new_prod_lot(self, cr, uid, ids, context=None):
        """ 
        Adds a new production lot and then assigns the id to the stock move.
        If the field is blank the new id will be the next in sequence
        Changes the Quantity of Product.
        @param self: The object pointer.
        @param cr: A database cursor
        @param uid: ID of the user currently logged in
        @param ids: List of IDs selected 
        @param context: A standard dictionary 
        @return:  
        """
        move_obj = self.pool.get('stock.move')
        move_ids = context['active_ids']
        for move in move_obj.browse(cr, uid, move_ids):
            if move.prodlot_id:
                return {}
            else:
                context['prodlot_name'] = False
                for result in self.browse(cr, uid, ids):
                    if result.prodlot_id:
                        context['prodlot_name'] = result.prodlot_id
                        print ids
                        move_obj.new_prod_lot(cr, uid, [move.id], context)
                    else:
                        print ids
                        move_obj.new_prod_lot(cr, uid, [move.id], context)

        return {}
    
wiz_new_prodlot()