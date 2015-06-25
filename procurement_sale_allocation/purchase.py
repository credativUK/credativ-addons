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
            'procurement_ids': fields.one2many('procurement.order', 'purchase_id', 'Procurements', readonly=True, copy=False),
            'order_line_unalloc': fields.one2many('purchase.order.line', 'order_id', 'Order Lines', domain=[('move_dest_id', '=', False)], readonly=True, copy=False),
        }

    def allocate_check_stock(self, cr, uid, ids, proc_ids, context=None):
        assert len(ids) == 1 and len(proc_ids) == 1, "This function only supports being called with a single purchase ID"
        purchase_line_obj = self.pool.get('purchase.order.line')
        procurement_obj = self.pool.get('procurement.order')
        uom_obj = self.pool.get('product.uom')
        po = self.browse(cr, uid, ids[0], context=context)
        for proc in procurement_obj.browse(cr, uid, proc_ids, context=context):
            pol_ids = purchase_line_obj.search(cr, uid, [('move_dest_id', 'in', (False, proc.move_id.id)), ('state', '!=', 'cancel'), ('order_id', '=', po.id), ('product_id', '=', proc.product_id.id)], context=context)
            pol_assign_id = False
            for line in purchase_line_obj.browse(cr, uid, pol_ids, context=context):
                purchase_uom_qty = uom_obj._compute_qty(cr, uid, proc.product_uom.id, proc.product_qty, line.product_uom.id)
                if line.product_qty >= purchase_uom_qty:
                    pol_assign_id = line.id
                    break
            if not pol_assign_id:
                return False
        return True

    def do_merge(self, cr, uid, ids, context=None):
        no_merge = self.allocate_check_restrict(cr, uid, ids, context=context)
        to_merge = list(set(ids) - set(no_merge))
        return super(PurchaseOrder, self).do_merge(cr, uid, to_merge, context=context)


    def action_cancel(self, cr, uid, ids, context=None):
        if context == None:
            context = {}
        ctx = context.copy()
        ctx.update({'psa_po_cancel': True})
        procurement_obj = self.pool.get('procurement.order')
        procurement_ids = procurement_obj.search(cr, uid, [('purchase_id', 'in', ids), ('state', '!=', 'cancel')], context=ctx)
        if procurement_ids:
            procurement_obj.write(cr, uid, procurement_ids, {'purchase_id': False}, context=ctx)
            procurement_obj.write(cr, uid, procurement_ids, {'procure_method': 'make_to_order'}, context=ctx)
        return super(PurchaseOrder, self).action_cancel(cr, uid, ids, context=ctx)

    def purchase_cancel(self, cr, uid, ids, context=None):
        wf_service = netsvc.LocalService("workflow")
        procurement_obj = self.pool.get('procurement.order')
        procurement_ids = procurement_obj.search(cr, uid, [('purchase_id', 'in', ids), ('state', '!=', 'cancel')], context=context)
        if procurement_ids:
            procurement_obj.write(cr, uid, procurement_ids, {'purchase_id': False}, context=context)
            procurement_obj.write(cr, uid, procurement_ids, {'procure_method': 'make_to_order'}, context=context)
        for (id, name) in self.name_get(cr, uid, ids):
            wf_service.trg_validate(uid, 'purchase.order', id, 'purchase_cancel', cr)
        return True

class PurchaseOrderLine(osv.Model):
    _inherit = 'purchase.order.line'

    def unlink(self, cr, uid, ids, context=None):
        procurement_obj = self.pool.get('procurement.order')
        procurement_ids_to_remove = []
        for line in self.browse(cr, uid, ids, context=context):
            if line.move_dest_id:
                procurement_ids_to_remove.extend(procurement.id for procurement in line.move_dest_id.procurements)
        if procurement_ids_to_remove:
            procurement_obj.write(cr, uid, procurement_ids_to_remove, {'purchase_id': False}, context=context)
            procurement_obj.write(cr, uid, procurement_ids_to_remove, {'procure_method': 'make_to_order'}, context=context)
        return super(PurchaseOrderLine, self).unlink(cr, uid, ids, context=context)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
