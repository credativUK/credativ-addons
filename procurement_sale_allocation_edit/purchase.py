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

class PurchaseOrder(osv.Model):
    _inherit = 'purchase.order'

    _columns = {
        'skip_pol_remove': fields.boolean('Skip Line Removal', help='Set temporarily to prevent the scheduler from removing PO lines in the case of an order edit'),
    }

    _defaults = {
        'skip_pol_remove': False,
    }

    def _fixup_created_picking(self, cr, uid, ids, line_moves, remain_moves, context):
        if context is None:
            context = {}
        move_obj = self.pool.get('stock.move')
        line_obj = self.pool.get('purchase.order.line')
        procurement_obj = self.pool.get('procurement.order')
        wf_service = netsvc.LocalService("workflow")

        proc_to_po = {}
        ctx = context.copy()
        ctx['skip_merge_pol'] = True
        ctx.update({'skip_merge_pol': True, 'psa_proc_removed': True})
        for purchase in self.browse(cr, uid, ids, context=context):
            purchase.write({'skip_pol_remove': True})
            # Get list of all procurements which are linked to this PO
            proc_ids = procurement_obj.search(cr, uid, [('purchase_id', '=', purchase.order_edit_id.id), ('purchase_id', '!=', False), ('state', 'not in', ('done', 'cancel'))], context=context)
            proc_to_po[purchase] = proc_ids

            # Remove PO line for all procurements so they all revert back to confirmed MTO
            procurement_obj.write(cr, uid, proc_ids, {'purchase_id': False, 'procure_method': 'make_to_order'}, context=ctx)
            purchase.write({'skip_pol_remove': False})

        # 3. Finish fixing the pickings
        res = super(PurchaseOrder, self)._fixup_created_picking(cr, uid, ids, line_moves, remain_moves, context=context)

        for purchase, proc_ids in proc_to_po.iteritems():
            # For each procurement attempt to allocate to this PO
            procurement_obj.write(cr, uid, proc_ids, {'purchase_id': purchase.id}, context=context)
            t, i = len(proc_ids), 0
            failed_proc_ids = []
            for proc_id in proc_ids:
                i += 1
                _logger.warning('PO Edit Conf, Part 2: %s/%s' % (i, t))
                cr.execute('SAVEPOINT procurement')
                try:
                    wf_service.trg_validate(uid, 'procurement.order', proc_id, 'button_check', cr)
                except osv.except_osv:
                    cr.execute('ROLLBACK TO SAVEPOINT procurement')
                    failed_proc_ids.append(proc_id)
                else:
                    cr.execute('RELEASE SAVEPOINT procurement')
                if failed_proc_ids:
                    procurement_obj.write(cr, uid, failed_proc_ids, {'purchase_id': False}, context=context)

                # For each failed allocation, if the sale line type is MTO, reset the procurement and change back to MTO
                if failed and proc.move_id.sale_line_id and proc.move_id.sale_line_id.type == 'make_to_order':
                    proc.refresh()
                    if proc.state == 'exception':
                        wf_service.trg_validate(uid, 'procurement.order', proc.id, 'button_restart', cr)
                    proc.refresh()
                    if proc.state == 'confirmed':
                        proc.write({'procure_method': 'make_to_order'}, context=context)

        return res

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
