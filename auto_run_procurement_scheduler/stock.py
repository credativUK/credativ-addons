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

class stock_move(osv.osv):
    
    _inherit = "stock.move"
    
    def action_done(self, cr, uid, ids, context=None):
        res = super(stock_move, self).action_done(cr, uid, ids, context=context)
        run_scheduler = False
        for move in self.browse(cr, uid, ids, context=context):
            if move.location_id.usage == 'production' and move.location_dest_id.usage == 'stock':
                run_scheduler = True
            if move.location_id.usage == 'supplier' and move.location_dest_id.usage == 'stock':
                run_scheduler = True

        if run_scheduler:
            compute_all_pool = self.pool.get('procurement.order.compute.all')
            id_ = compute_all_pool.create(cr, uid, {})
            compute_all_pool.procure_calculation(cr, uid, [id_], {})

        return res

stock_move()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: