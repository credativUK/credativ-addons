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
from crm_claim import crm_claim

class sale_order_claim(osv.osv):
    '''
    Sale order claim. This model specialises crm.claim for making
    claims against sale orders. It assumes that the crm.claim.ref
    fields points to a sale.order resource and transfers this property
    into its own sale_order_line field.
    '''
    _inherit = 'crm.claim'
    _name = 'sale.order.claim'
    _description = 'Claim against a sale order'

    # def _get_order_id(self, cr, uid, ids, field_name, arg, context=None):
    #     return dict([(claim.id, int(claim.ref[claim.ref.find(',') + 1:]))
    #                  for claim in self.browse(cr, uid, ids, context=context)
    #                  if claim.ref[:claim.ref.find(',') == 'sale.order']])

    def write(self, cr, uid, ids, vals, context=None):
        if 'sale_order_id' in vals and 'ref' not in vals:
            vals['ref'] = 'sale.order,%d' % vals['sale_order_id']
        return super(crm_claim, self).write(cr, uid, ids, vals, context=context)

    _columns = {
        'sale_order_id': fields.many2one(
            'sale.order',
            'Sale order',
            required=True),
        # 'sale_order_id': fields.function(
        #     _get_order_id,
        #     method=True,
        #     type='many2one',
        #     relation='sale.order',
        #     readonly=True,
        #     required=True,
        #     string='Sale order',
        #     store={'crm.claim': (lambda self, cr, uid, ids, ctx: ids, ['ref'], 10)}),
        # 'order_ref': fields.related(
        #     'sale_order_id',
        #     'name',
        #     type='char',
        #     readonly=True,
        #     string='Order ref.'),
        'whole_order_claim': fields.boolean(
            'Claim against whole order',
            required=True),
        'shop_id': fields.related(
            'sale_order_id', 'shop_id',
            type='many2one',
            relation='sale.shop',
            readonly=True,
            string='Shop'),
        'origin': fields.related(
            'sale_order_id',
            'origin',
            type='char',
            readonly=True,
            string='Source document'),
        'client_order_ref': fields.related(
            'sale_order_id',
            'client_order_ref',
            type='char',
            readonly=True,
            string='Customer ref.'),
        'order_state': fields.related(
            'sale_order_id',
            'state',
            type='char',
            readonly=True,
            string='Order state'),
        'date_order': fields.related(
            'sale_order_id',
            'date_order',
            type='date',
            string='Order date',
            readonly=True),
        'merchandiser_id': fields.related(
            'sale_order_id', 'user_id',
            type='many2one',
            relation='res.users',
            readonly=True,
            string='Merchandiser'),
        'customer_id': fields.related(
            'sale_order_id', 'partner_id',
            type='many2one',
            relation='res.partner',
            readonly=True,
            string='Customer'),
        'partner_shipping_id': fields.related(
            'sale_order_id', 'partner_shipping_id',
            type='many2one',
            relation='res.partner.address',
            readonly=True,
            string='Customer shipping addr.'),
        'shipped': fields.related(
            'sale_order_id',
            'shipped',
            type='boolean',
            readonly=True,
            string='Shipped?'),
        'invoiced': fields.related(
            'sale_order_id',
            'invoiced',
            type='boolean',
            readonly=True,
            string='Invoiced?'),
        'order_total': fields.related(
            'sale_order_id',
            'amount_total',
            type='float',
            readonly=True,
            string='Order total'),
        'order_issue_ids': fields.one2many(
            'sale.order.issue',
            'order_claim_id',
            string='Claim issues',
            oldname='claim_line_ids'),
        }

    _defaults = {
        'name': lambda self, cr, uid, ctx: self.pool.get('ir.sequence').next_by_code(cr, uid, 'sale.order.claim'),
        'whole_order_claim': False,
        }

sale_order_claim()


class sale_order_issue(osv.osv):
    '''
    Sale order issue. This model specialises crm.claim.line for
    logging issues against specific parts of a sale order. It parses
    crm.claim.line.resource as either a sale.order.line resource or a
    stock.move resource, storing a reference in either
    sale_order_line_id or stock_move_id.
    '''
    _inherit = 'crm.claim.line'
    _name = 'sale.order.issue'
    _description = 'Individual issue in a sale order claim'

    def _get_related(self, cr, uid, ids, context=None):
        '''This method parses the .resource field into (model, res_id)
        pairs, returning a dict with one pair for each resource in
        ids.'''
        return dict([(line.id, (line.resource[:line.resource.find(',')], int(line.resource[line.resource.find(',') + 1:])))
                     for line in self.browse(cr, uid, ids, context=context)])

    def _sm2sol(self, cr, uid, sm_id, context=None):
        ol_pool = self.pool.get('sale.order.line')
        try:
            # FIXME In the case that a sale.order.line is referred to,
            # we'll just pick the first stock.move from that
            # sale.order.line. How bad is this?
            return ol_pool.browse(self, cr, uid, sm_id, context=context).move_ids[0]
        except IndexError:
            return False

    def _sol2sm(self, cr, uid, sol_id, context=None):
        return self.pool.get('stock.move').browse(self, cr, uid, sol_id, context=context).sale_line_id

    _convert = {
        ('sock.move', 'stock.move'): lambda self, cr, uid, sm_id, ctx: sm_id,
        ('stock.move', 'sale.order.line'): _sm2sol,
        ('sale.order.line', 'sale.order.line'): lambda self, cr, uid, sol_id, ctx: sol_id,
        ('sale.order.line', 'stock.move'): _sol2sm,
        }
    '''_convert stores functions for getting IDs of one model given
    IDs of another. Each entry is index by a 2-tuple containing:
    (model_in, model_out).'''

    def _get_stock_move(self, cr, uid, ids, field_name, arg, context=None):
        return dict([(id, self._convert[(model, 'stock.move')](self, cr, uid, id, context=context))
                     for id, (model, res_id) in self._get_related(cr, uid, ids, context=context).items()])

    def _get_sale_order_line(self, cr, uid, ids, field_name, arg, context=None):
        return dict([(id, self._convert[(model, 'sale.order.line')](self, cr, uid, id, context=context))
                     for id, (model, res_id) in self._get_related(cr, uid, ids, context=context).items()])

    _columns = {
        'sale_order_line_id': fields.function(
            _get_sale_order_line,
            method=True,
            type='many2one',
            relation='sale.order.line',
            readonly=True,
            string='Order line',
            store={'crm.claim.line': (lambda self, cr, uid, ids, ctx: ids, ['resource'], 10)}),
        'stock_move_id': fields.function(
            _get_stock_move,
            method=True,
            type='many2one',
            relation='stock.move',
            readonly=True,
            string='Stock move',
            store={'crm.claim.line': (lambda self, cr, uid, ids, ctx: ids, ['resource'], 10)}),
        'order_claim_id': fields.many2one(
            'sale.order.claim',
            string='Claim',
            required=True,
            oldname='claim_id'),
        'date': fields.related(
            'stock_move_id', 'date',
            type='date',
            relation='stock.move',
            readonly=True,
            string='Move date'),
        'product': fields.related(
            'stock_move_id', 'product_id', 'name',
            type='char',
            relation='product.product',
            readonly=True,
            string='Product'),
        'product_qty': fields.related(
            'stock_move_id', 'product_qty',
            type='float',
            relation='stock.move',
            readonly=True,
            string='Quantity'),
        'move_state': fields.related(
            'stock_move_id', 'state',
            type='char',
            relation='stock.move',
            readonly=True,
            string='State'),
        'price_unit': fields.related(
            'stock_move_id', 'price_unit',
            type='float',
            relation='stock.move',
            readonly=True,
            string='Unit price'),
        # TODO Consider adding any fields from sale.order.line
        }

    # def _ensure_claim_is_sale_order_claim(self, cr, uid, ids, context=None):
    #     return all([line.claim_id.ref[:line.claim_id.ref.find(',')] == 'sale.order'
    #                 for line in self.browse(cr, uid, ids, context=context)])

    # _constraints = [
    #     (_ensure_claim_is_sale_order_claim,
    #      'Parent claim of an order issue must be a claim against a sale order.',
    #      ['claim_id']),
    #     ]

sale_order_issue()
