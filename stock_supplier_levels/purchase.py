# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright 2015 credativ Ltd
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

from openerp.osv import osv, fields

class PurchaseOrder(osv.osv):
    _inherit = "purchase.order"

    _columns = {
        'force_reduce_supplier': fields.boolean('Force Reduce Supplier Stock', readonly=True, states={'draft':[('readonly', False)]}, copy=False,
                                                help="When set this will override the settings on all purchase lines to reduce the supplier stock level on order confirmation."),
    }

    _defaults = {
        'force_reduce_supplier': False,
    }

    def onchange_reduce_supplier(self, cr, uid, ids, force_reduce_supplier, order_line, context=None):
        if context is None:
            context = {}
        pol_obj = self.pool.get('purchase.order.line')
        line_values = []

        for purchase_line in order_line:
            if purchase_line[0] in (0, 1): # Add / Existing Update
                purchase_line[2].update({'reduce_supplier': force_reduce_supplier})
                line_values.append(purchase_line)
            elif purchase_line[0] == 2: # Delete
                line_values.append(purchase_line)
            elif purchase_line[0] == 4: # Update
                line_values.append((1, purchase_line[1], {'reduce_supplier': force_reduce_supplier}))
            else:
                raise NotImplementedError('Unable to handle lines with type %d' % (purchase_line[0],))

        values = {'order_line': line_values}
        return {'value': values }

class PurchaseOrderLine(osv.osv):
    _inherit = "purchase.order.line"

    _columns = {
        'reduce_supplier': fields.boolean('Reduce Supplier Stock', readonly=True, states={'draft':[('readonly', False)]}, copy=False,
                                          help="When set and the order is confirmed, the supplier stock level will be reduced by the order quantity to offset the new incoming stock"),
    }

    _defaults = {
        'reduce_supplier': False,
    }

    def action_confirm(self, cr, uid, ids, context=None):
        move_obj = self.pool.get('stock.move')
        res = super(PurchaseOrderLine, self).action_confirm(cr, uid, ids, context=context)
        reduce_data = {} # (product_id, uom_id, warehouse_id, partner_id): [qty, date, comment]
        for pol in self.browse(cr, uid, ids, context=context):
            if pol.product_id and (pol.reduce_supplier or pol.order_id.force_reduce_supplier):
                key = (pol.product_id.id, pol.product_uom.id, pol.order_id.warehouse_id.id, pol.order_id.partner_id.id)
                reduce_data.setdefault(key, [0.0, False, False])
                reduce_data[key][0] += pol.product_qty
                reduce_data[key][1] = pol.order_id.date_order
                reduce_data[key][2] = pol.order_id.name
        if reduce_data:
            move_obj.reduce_supplier_stock(cr, uid, reduce_data, context=context)
        return res

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: