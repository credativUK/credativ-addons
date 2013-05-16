# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution    
#    Copyright (C) 2013 credativ ltd (<http://www.credativ.co.uk>). All Rights Reserved
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

class purchase_order_line(osv.osv):
    _inherit = 'purchase.order.line'
    _order = 'product_name asc'
    
    def _get_lines_from_products(self, cr, uid, product_ids, context=None):
        res = set()
        for product in product_ids:
            ids = self.pool.get('purchase.order.line').search(cr, uid, [('product_id', '=', product),], context=context)
            res.update(ids)
        return list(res)
    
    _columns = {
            'product_name': fields.related('product_id', 'name', string='Product', type='char',
                    store={
                            'purchase.order.line': (lambda self, cr, uid, ids, ctx: ids, ['product_id'], 10),
                            'product.product': (_get_lines_from_products, ['name', 'name_template'], 10),
                          })
        }

purchase_order_line()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: