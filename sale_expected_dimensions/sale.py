# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 credativ Ltd (<http://credativ.co.uk>).
#    All Rights Reserved
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
from collections import defaultdict

class sale_order(osv.osv):
    _inherit = 'sale.order'

    def _cal_dimensions(self, cr, uid, ids, field_name, arg, context=None):
        if type(field_name) not in (list, tuple):
            field_name = [field_name]
        sol_obj = self.pool.get('sale.order.line')
        res = defaultdict(dict)
        line_ids = sol_obj.search(cr, uid, [('order_id','in', ids)], context=context)
        for line in sol_obj.read(cr, uid, line_ids, ['order_id'] + field_name, context=context):
            order_id = line['order_id'][0]
            for field in field_name:
                res[order_id][field] = res[order_id].get(field, 0) + line[field]
        return res

    def _get_order_line(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('sale.order.line').browse(cr, uid, ids, context=context):
            result[line.order_id.id] = True
        return result.keys()

    _columns = {
            'weight': fields.function(_cal_dimensions, string="Expected weight", type='float', multi='_cal_dimensions',
                    help="The expected weight in Kg.",
                    store={
                    'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line'], 20),
                    'sale.order.line': (_get_order_line, ['product_id','product_qty','product_uom'], 20),
                    }),
            'weight_net': fields.function(_cal_dimensions, string="Expected net weight", type='float', multi='_cal_dimensions',
                    help="The expected net weight in Kg.",
                    store={
                    'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line'], 20),
                    'sale.order.line': (_get_order_line, ['product_id','product_qty','product_uom'], 20),
                    }),
            'volume': fields.function(_cal_dimensions, string="Expected volume", type='float', multi='_cal_dimensions',
                    help="The expected volume in m3.",
                    store={
                    'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line'], 20),
                    'sale.order.line': (_get_order_line, ['product_id','product_qty','product_uom'], 20),
                    }),
    }

sale_order()

class sale_order_line(osv.osv):
    _inherit = 'sale.order.line'

    def _cal_line_dimensions(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        uom_obj = self.pool.get('product.uom')
        for line in self.browse(cr, uid, ids, context=context):
            if line.product_id.weight > 0.00 or line.product_id.weight_net > 0.00 or line.product_id.volume > 0.00:
                res[line.id] = {}
                converted_qty = line.product_uom_qty

                if line.product_uom.id <> line.product_id.uom_id.id:
                    converted_qty = uom_obj._compute_qty(cr, uid, line.product_uom.id, line.product_qty, line.product_id.uom_id.id)

                res[line.id]['weight'] = (converted_qty * line.product_id.weight)
                res[line.id]['weight_net'] = (converted_qty * line.product_id.weight_net)
                res[line.id]['volume'] = (converted_qty * line.product_id.volume)
        return res

    _columns = {
            'weight': fields.function(_cal_line_dimensions, string="Expected weight", type='float', multi='_cal_line_dimensions',
                    help="The expected weight in Kg.",
                    store={
                    'sale.order.line': (lambda self, cr, uid, ids, c=None: ids, ['product_id', 'product_qty', 'product_uom'], 20),
                    }),
            'weight_net': fields.function(_cal_line_dimensions, string="Expected net weight", type='float', multi='_cal_line_dimensions',
                    help="The expected net weight in Kg.",
                    store={
                    'sale.order.line': (lambda self, cr, uid, ids, c=None: ids, ['product_id', 'product_qty', 'product_uom'], 20),
                    }),
            'volume': fields.function(_cal_line_dimensions, string="Expected volume", type='float', multi='_cal_line_dimensions',
                    help="The expected volume in m3.",
                    store={
                    'sale.order.line': (lambda self, cr, uid, ids, c=None: ids, ['product_id', 'product_qty', 'product_uom'], 20),
                    }),
    }


sale_order_line()
