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

    def action_in_production(self, cr, uid, ids):
        res = super(mrp_production, self).action_in_production(cr, uid, ids)
        #assigns a unique production lot id to finished products suffixed by sub contractor code
        move_obj = self.pool.get('stock.move')
        seq_obj = self.pool.get('ir.sequence')
        prodlot_obj = self.pool.get('stock.production.lot')
        for production in self.browse(cr, uid, ids):
            prodlot_name = seq_obj.get(cr,uid, 'stock.lot.serial')
            for move in production.move_lines:
                # TODO (derek.sheridan@credativ.co.uk): remove hard coding
                # The production lot name should change only if bom type is automatic and prodlot_id of stock move ends at FA
                if production.bom_id and production.bom_id.type == 'automatic':
                    if move.prodlot_id and move.prodlot_id.name.endswith('FA'):
                        prodlot_name += '-' + move.prodlot_id.name
            finished_prodlot_id = prodlot_obj.create(cr, uid, {
                'product_id': production.product_id.id,
                'name': prodlot_name
            })
            move_obj.write(cr, uid, [move.id for move in production.move_created_ids],
                           {'prodlot_id': finished_prodlot_id})        
        return res

mrp_production()
