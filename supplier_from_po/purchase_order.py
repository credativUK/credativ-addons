# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2013 credativ Ltd (<http://credativ.co.uk>).
#    All Rights Reserved
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

from osv import osv

class purchase_order(osv.osv):
    _inherit = 'purchase.order'

    def wkf_approve_order(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        res = super(purchase_order, self).wkf_approve_order(cr, uid, ids, context=context)
        supplier_pool = self.pool.get('product.supplierinfo')
        for order in self.browse(cr, uid, ids, context=context):
            for po_line in order.order_line:
                # check if supplier already exists in the supplier list for this product
                if order.partner_id.id not in [x.name.id for x in po_line.product_id.seller_ids]:
                    # add supplier to supplierinfo for product
                    supplier_vals = {'name': order.partner_id.id,
                                    'product_id': po_line.product_id.id,
                                    'min_qty': 0,
                                    'delay': 0,
                                    }
                    supplier_pool.create(cr, uid, supplier_vals, context=context)

purchase_order()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
