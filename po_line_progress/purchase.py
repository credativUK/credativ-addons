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

from openerp.osv import orm, fields, osv

class PurchaseOrderLine(orm.Model):
    _inherit = "purchase.order.line"

    def _transferred_rate(self, cr, uid, ids, field_name, arg, context=None):
        uom_obj = self.pool.get("product.uom")
        res = {}
        for line in self.browse(cr, uid, ids, context=context):
            product_uom = line.product_id.uom_id
            transferred, total = 0, 0
            for move in line.move_ids:
                if move.state in ('draft', 'cancel'):
                    continue
                qty = uom_obj._compute_qty(cr, uid, move.product_uom.id,
                                           move.product_qty, product_uom.id)
                total += qty
                if move.state == 'done':
                    transferred += qty
            res[line.id] = {
                'transferred_rate': "%r / %r" % (transferred, total),
                'partially_received': transferred and transferred < total,
            }
        return res

    _columns = {
        'transferred_rate': fields.function(_transferred_rate,
            string='Goods transferred', type='char', multi="transferred",
            help="How much of this order line has been transferred"),
        'partially_received': fields.function(_transferred_rate,
            string='Partially received', type='boolean', multi="transferred",
            help="True if the order line is only partially received"),
    }
