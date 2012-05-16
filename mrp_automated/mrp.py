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

class mrp_production(osv.osv):

    _inherit = "mrp.production"

    def action_confirm(self, cr, uid, ids):

    res = super(mrp_production, self).action_confirm(cr, uid, ids)
	#assigns a unique production lot id to finished products prefixed by sub contractor code
        move_obj = self.pool.get('stock.move')
        seq_obj = self.pool.get('ir.sequence')
        prodlot_obj = self.pool.get('stock.production.lot')
        prodlot_name = seq_obj.get(cr,uid, 'stock.lot.serial')
        for production in self.browse(cr, uid, ids):
            if not production.product_lines:
                self.action_compute(cr, uid, [production.id])
                production = self.browse(cr, uid, [production.id])[0]		
        finished_prodlot_data = {
            'product_id': production.product_id.id,
            'name': prodlot_name,
            'prefix': production.bom_id.routing_id.code,
            }
        finished_prodlot_id = prodlot_obj.create(cr, uid, finished_prodlot_data)
        data = {
            'prodlot_id': finished_prodlot_id,
        }                
        stock_move_id = move_obj.search(cr, uid, [('name','=','PROD:' + production.name),('date','=',production.date_planned),('location_id','=',7)])[0]
        move_obj.write(cr, uid, stock_move_id, data, context=None)
        
        return res

mrp_production()