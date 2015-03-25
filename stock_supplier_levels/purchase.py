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
        for pol in self.browse(cr, uid, ids, context=context):
            if pol.product_id and (pol.reduce_supplier or pol.order_id.force_reduce_supplier):
                move_obj.reduce_supplier_stock(cr, uid, pol.product_id.id, pol.product_uom.id, pol.product_qty, pol.order_id.partner_id.id, pol.order_id.warehouse_id.id, pol.order_id.date_order, pol.order_id.name, context=context)
        return res

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: