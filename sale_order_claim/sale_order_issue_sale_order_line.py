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

class sale_order_issue(osv.osv):
    '''
    Add columns and methods for making sale.order.issues against a
    sale.order.line.
    '''
    _inherit = 'sale.order.issue'
    _description = 'Sale order issue against a sale order line'

    def _find_records_for_order(self, cr, uid, order_id, context=None):
        ol_pool = self.pool.get('sale.order.line')
        return ol_pool.browse(cr, uid,
                              ol_pool.search(cr, uid, [('order_id','=',order_id)], context=context),
                              context=context)

    def _make_issue_dict(self, cr, uid, claim_id, rec, context=None):
        res = dict([(col, False) for col in self._columns.keys()])
        res.update({'resource': 'sale.order.line,%d' % (rec.id,),
                    'order_claim_id': claim_id,
                    'select': False,
                    'sale_order_line_id': rec.id})
        return res

    def write(self, cr, uid, ids, vals, context=None):
        if 'sale_order_line_id' in vals and 'resource' not in vals:
            vals['resource'] = 'sale.order.line,%d' % vals['sale_order_line_id']
        return super(sale_order_issue, self).write(cr, uid, ids, vals, context=context)

    _columns = {
        'sale_order_line_id': fields.many2one(
            'sale.order.line',
            string='Order line'),
        'ol_product': fields.related(
            'sale_order_line_id', 'product_id', 'name',
            type='char',
            relation='product.product',
            readonly=True,
            string='Product'),
        'ol_price_unit': fields.related(
            'sale_order_line_id', 'price_unit',
            type='float',
            relation='sale.order.line',
            readonly=True,
            string='Price'),
        'ol_product_uos_qty': fields.related(
            'sale_order_line_id', 'product_uos_qty',
            type='float',
            relation='sale.order.line',
            readonly=True,
            string='Qty'),
        'ol_state': fields.related(
            'sale_order_line_id', 'state',
            type='char',
            relation='sale.order.line',
            readonly=True,
            string='State'),
        }

sale_order_issue()
