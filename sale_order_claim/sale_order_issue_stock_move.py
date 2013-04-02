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
    stock.move.
    '''
    _inherit = 'sale.order.issue'
    _description = 'Sale order issue against a stock move'

    def _find_records_for_order(self, cr, uid, order_id, context=None):
        sm_pool = self.pool.get('stock.move')
        return sm_pool.browse(cr, uid,
                              sm_pool.search(cr, uid, [('sale_id','=',order_id)], context=context),
                              context=context)

    def _make_issue_dict(self, cr, uid, claim_id, rec, context=None):
        res = dict([(col, False) for col in self._columns.keys()])
        res.update({'resource': 'stock.move,%d' % (rec.id,),
                    'order_claim_id': claim_id,
                    'select': False,
                    'stock_move_id': rec.id})
        return res

    def _issue_eq_res(self, cr, uid, issue, res, context=None):
        return 'stock_move_id' in issue and\
            issue['stock_move_id'] == res.id

    def write(self, cr, uid, ids, vals, context=None):
        if 'stock_move_id' in vals and 'resource' not in vals:
            vals['resource'] = 'stock.move,%d' % vals['stock_move_id']
        return super(sale_order_issue, self).write(cr, uid, ids, vals, context=context)

    _columns = {
        'stock_move_id': fields.many2one(
            'stock.move',
            string='Stock move'),
        'sm_date': fields.related(
            'stock_move_id', 'date',
            type='date',
            relation='stock.move',
            readonly=True,
            string='Move date'),
        'sm_product': fields.related(
            'stock_move_id', 'product_id', 'name',
            type='char',
            relation='product.product',
            readonly=True,
            string='Product'),
        'sm_product_qty': fields.related(
            'stock_move_id', 'product_qty',
            type='float',
            relation='stock.move',
            readonly=True,
            string='Quantity'),
        'sm_state': fields.related(
            'stock_move_id', 'state',
            type='char',
            relation='stock.move',
            readonly=True,
            string='State'),
        'sm_price_unit': fields.related(
            'stock_move_id', 'price_unit',
            type='float',
            relation='stock.move',
            readonly=True,
            string='Unit price'),
        }

sale_order_issue()
