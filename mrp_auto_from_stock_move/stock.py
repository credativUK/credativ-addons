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

class stock_move(osv.osv):
    
    _inherit = "stock.move"

    def write(self, cr, uid, ids, vals, context=None):
        # the logic of the existing check in write gives an error if someone other than uid 1 (admin) 
        # tries to write to a stock_move that is already in state done. That error is now being bypassed
        # if values being written do not change the existing ones.
        move = self.browse(cr, uid, ids)
        frozen_fields = set(['product_qty', 'product_uom', 'product_uos_qty', 'product_uos', 'location_id', 'location_dest_id', 'product_id'])
        new_uid = uid
        
        for field in frozen_fields:
            if field in vals and hasattr(move, field) and getattr(move, field) != vals[field]:
                break
        else:
            new_uid = 1

        return super(stock_move, self).write(cr, new_uid, ids, vals, context=context)

stock_move()