# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.osv import osv


class stock_return_picking(osv.osv_memory):
    _inherit = 'stock.return.picking'

    def get_return_history(self, cr, uid, pick_id, context=None):
        """
         Get  return_history.
         @param self: The object pointer.
         @param cr: A database cursor
         @param uid: ID of the user currently logged in
         @param pick_id: Picking id
         @param context: A standard dictionary
         @return: A dictionary which of values.
        """
        pick_obj = self.pool.get('stock.picking')
        pick = pick_obj.browse(cr, uid, pick_id, context=context)
        return_history = {}
        for m in pick.move_lines:
            if m.state == 'done':
                return_history[m.id] = 0
                for rec in m.move_history_ids2:
                    # only take into account 'product return' moves, ignoring
                    # any other kind of upstream moves, such as internal
                    # procurements, etc. a valid return move will be the
                    # exact opposite of ours:
                    #     (src location, dest location) <=> (dest location, src location))
                    # Fix : Ignore moves in cancel state
                    if rec.location_dest_id.id == m.location_id.id \
                            and rec.location_id.id == m.location_dest_id.id \
                            and rec.state != 'cancel':
                        return_history[m.id] += (rec.product_qty * rec.product_uom.factor)
        return return_history

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
