# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 credativ ltd (<http://www.credativ.co.uk>). All Rights Reserved
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

from osv import osv, fields
from openerp.tools.translate import _
import netsvc

class SaleOrder(osv.Model):
    _inherit = 'sale.order'

    def _fixup_created_picking(self, cr, uid, line_moves, remain_moves, context):
        move_obj = self.pool.get('stock.move')
        procurement_obj = self.pool.get('procurement.order')
        wf_service = netsvc.LocalService("workflow")

        if remain_moves is not None:
            procurement_pos = {}

            for line_id, old_moves in remain_moves.iteritems():
                proc_ids = procurement_obj.search(cr, uid, [('move_id', 'in', [x.id for x in old_moves]), ('state', 'not in', ('cancel', 'done')), ('purchase_id', '!=', False)], context=context)
                if proc_ids:
                    for proc in procurement_obj.browse(cr, uid, proc_ids, context=context):
                        procurement_pos.setdefault(proc.product_id.id, set()).add(proc.purchase_id.id)
                    procurement_obj.write(cr, uid, proc_ids, {'purchase_id': False}, context=context)

            for line_id, old_moves in remain_moves.iteritems():
                line = self.pool.get('sale.order.line').browse(cr, uid, line_id)
                proc_ids = procurement_obj.search(cr, uid, [('move_id', 'in', [x.id for x in line.move_ids]), ('state', 'not in', ('cancel', 'done')), ('purchase_id', '=', False)], context=context)
                if proc_ids:
                    for proc in procurement_obj.browse(cr, uid, proc_ids, context=context):
                        for po_id in procurement_pos.get(proc.product_id.id, []):
                            # We use a savepoint here since we want to attempt to allocate the procurement to the previous PO
                            # it is allowed to fail but we don't want to be in an inconsistant state
                            cr.execute('SAVEPOINT procurement')
                            try:
                                procurement_obj.write(cr, uid, [proc.id], {'purchase_id': po_id, 'procure_method': 'make_to_order'}, context=context)
                                wf_service.trg_validate(uid, 'procurement.order', proc.id, 'button_check', cr)
                            except osv.except_osv:
                                cr.execute('ROLLBACK TO SAVEPOINT procurement')
                                break
                            else:
                                cr.execute('RELEASE SAVEPOINT procurement')

        return super(SaleOrder, self)._fixup_created_picking(cr, uid, line_moves, remain_moves, context=context)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
