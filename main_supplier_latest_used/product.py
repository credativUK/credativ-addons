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

from osv import osv, fields

class product_template(osv.osv):
    _inherit = "product.template"

    def _get_main_product_supplier(self, cr, uid, product, context=None):
        """Determines the main (best) product supplier for ``product``, 
        returning the corresponding ``supplierinfo`` record, or False
        if none were found. This function overwrites the default strategy to select the
        supplier with the highest priority (i.e. smallest sequence).  Instead, this function 
        selects the supplier most recently used on a purchase order.

        :param browse_record product: product to supply
        :rtype: product.supplierinfo browse_record or False
        """
        seller_ids = [seller_info.name.id for seller_info in product.seller_ids or []]
        if seller_ids:
            cr.execute('''SELECT partner_id FROM purchase_order_line
                        WHERE product_id = %s
                        AND partner_id IN %s
                        ORDER BY COALESCE(write_date, create_date) DESC''', (product.id, tuple(seller_ids)))
                        # Use coalesce for cases where write_date field is not populated
            seller_id = cr.fetchone()
            if seller_id:
                seller = [seller_info for seller_info in product.seller_ids if seller_info.name.id == seller_id[0]]
                return seller and seller[0] or False
            else:
                # Take first supplier ordered by sequence - if no purchase orders for product
                sellers_by_sequence = [(seller_info.sequence, seller_info) for seller_info in product.seller_ids or []]
                sellers_by_sequence.sort()
                return sellers_by_sequence and sellers_by_sequence[0][1] or False
        return False

    def _calc_seller(self, cr, uid, ids, fields, arg, context=None):
        result = {}
        for product in self.browse(cr, uid, ids, context=context):
            main_supplier = self._get_main_product_supplier(cr, uid, product, context=context)
            result[product.id] = {
                'seller_info_id': main_supplier and main_supplier.id or False,
                'seller_delay': main_supplier and main_supplier.delay or 1,
                'seller_qty': main_supplier and main_supplier.qty or 0.0,
                'seller_id': main_supplier and main_supplier.name.id or False
            }
        return result
        
    def _get_supplierinfo_prod_tmpl_ids(self, cr, uid, supplierinfo_ids, context=None):
        res = []
        for supplierinfo in self.pool.get('product.supplierinfo').browse(cr, uid, supplierinfo_ids, context):
            res.append(supplierinfo.product_id.id)
        return res

    def _get_purchase_order_line_prod_tmpl_ids(self, cr, uid, purchase_order_line_ids, context=None):
        res = []
        for purchase_order_line in self.pool.get('purchase.order.line').browse(cr, uid, purchase_order_line_ids, context):
            res.append(purchase_order_line.product_id.id)
        return res
        
    _columns = {
        'seller_info_id': fields.function(_calc_seller, type='many2one', relation="product.supplierinfo", multi="seller_info", store={
                'product.template': (lambda self, cr, uid, ids, ctx: ids, ['seller_ids'], 10),
                'product.supplierinfo': (_get_supplierinfo_prod_tmpl_ids, ['sequence', 'delay', 'min_qty', 'name', 'product_id'], 10),
                'purchase.order.line': (_get_purchase_order_line_prod_tmpl_ids, ['partner_id', 'product_id'], 10),
                }),
        'seller_delay': fields.function(_calc_seller, type='integer', string='Supplier Lead Time', multi="seller_info", help="This is the average delay in days between the purchase order confirmation and the reception of goods for this product and for the default supplier. It is used by the scheduler to order requests based on reordering delays.", store={
                'product.template': (lambda self, cr, uid, ids, ctx: ids, ['seller_ids'], 10),
                'product.supplierinfo': (_get_supplierinfo_prod_tmpl_ids, ['sequence', 'delay', 'min_qty', 'name', 'product_id'], 10),
                'purchase.order.line': (_get_purchase_order_line_prod_tmpl_ids, ['partner_id', 'product_id'], 10),
                }),
        'seller_qty': fields.function(_calc_seller, type='float', string='Supplier Quantity', multi="seller_info", help="This is minimum quantity to purchase from Main Supplier.", store={
                'product.template': (lambda self, cr, uid, ids, ctx: ids, ['seller_ids'], 10),
                'product.supplierinfo': (_get_supplierinfo_prod_tmpl_ids, ['sequence', 'delay', 'min_qty', 'name', 'product_id'], 10),
                'purchase.order.line': (_get_purchase_order_line_prod_tmpl_ids, ['partner_id', 'product_id'], 10),
                }),
        'seller_id': fields.function(_calc_seller, type='many2one', relation="res.partner", string='Main Supplier', help="Main Supplier who has been most recently used in a purchase order.", multi="seller_info", store={
                'product.template': (lambda self, cr, uid, ids, ctx: ids, ['seller_ids'], 10),
                'product.supplierinfo': (_get_supplierinfo_prod_tmpl_ids, ['sequence', 'delay', 'min_qty', 'name', 'product_id'], 10),
                'purchase.order.line': (_get_purchase_order_line_prod_tmpl_ids, ['partner_id', 'product_id'], 10),
                }),
     }

product_template()
