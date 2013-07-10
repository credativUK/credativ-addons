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
            partner_id = order.partner_id.id
            # list of unique products to prevent duplication of same supplier when multiple lines added for same product
            unique_products = set([order_line.product_id for order_line in order.order_line])
            for product in unique_products:
                # check if supplier already exists in the supplier list for this product
                if partner_id not in [x.name.id for x in product.seller_ids]:
                    # add supplier to supplierinfo for product
                    next_sequence =  (product.seller_ids and max([sup.sequence for sup in product.seller_ids]) or 0) + 1
                    supplier_vals = {'name': partner_id,
                                    'product_id': product.id,
                                    'min_qty': 0,
                                    'delay': 0,
                                    'sequence': next_sequence,
                                    }
                    supplier_pool.create(cr, uid, supplier_vals, context=context)

purchase_order()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
