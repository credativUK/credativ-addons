# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2014 credativ Ltd (<http://credativ.co.uk>).
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

class stock_move(osv.osv):
    _inherit = 'stock.move'

    _columns = {
            'product_unit_cost' : fields.float('Unit Cost', help="The product's unit cost at the time of this move's creation.", readonly=True),
            'inventory_line_id' : fields.many2one('stock.inventory.line', 'Inventory Line', help='The Stock Inventory Line from which this move was generated.'),
    }

    _defaults = {
            'product_unit_cost' : 0.0,
    }

    def _get_product_cost(self, cr, uid, ids, prod_id, *args, **kwargs):
        values = {'product_unit_cost' : 0.0}
        if prod_id:
            uom_obj = self.pool.get('product.uom')
            prod_obj = self.pool.get('product.product')
            prod_inf = prod_obj.read(cr, uid, prod_id, ['standard_price','uom_id'], context=kwargs.get('context'))
            prod_cst = prod_inf.get('standard_price')
            prod_uom = prod_inf.get('uom_id', (None,))[0]
            if prod_cst and prod_uom:
                per_qty_price = uom_obj._compute_price(cr, uid, prod_uom, prod_cst)
                values.update({'product_unit_cost' : per_qty_price})
        return values


    def onchange_product_id(self, *args, **kwargs):
        res = super(stock_move, self).onchange_product_id(*args, **kwargs)
        res.setdefault('value', {}).update(self._get_product_cost(*args, **kwargs))
        return res

    def write(self, cr, uid, ids, values, context=None):
        prod_id = values.get('product_id')
        uom = values.get('product_uom')
        if prod_id:
            cost_val = self._get_product_cost(cr, uid, ids, prod_id, uom, context=context)
            values.update(cost_val)
        return super(stock_move, self).write(cr, uid, ids, values, context=context)


    def create(self, cr, uid, values, context=None):
        prod_id = values.get('product_id' , False)
        uom = values.get('product_uom', False)
        cost_val = self._get_product_cost(cr, uid, [], prod_id, uom, context=context)
        values.update(cost_val)
        return super(stock_move, self).create(cr, uid, values, context=context)

stock_move()

class stock_inventory(osv.osv):
    _inherit = 'stock.inventory'

    def _inventory_line_hook(self, cr, uid, inventory_line, move_vals):
        move_vals.update({'inventory_line_id' : inventory_line.id})
        return super(stock_inventory, self)._inventory_line_hook(cr, uid, inventory_line, move_vals)

stock_inventory()

class stock_inventory_line(osv.osv):
    _inherit = 'stock.inventory.line'

    def _calc_financial_impact(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        ids = isinstance(ids, list) and ids or [ids]
        for id in ids:
            uom_obj  = self.pool.get('product.uom')
            move_obj = self.pool.get('stock.move')
            prod_obj = self.pool.get('product.product')
            move_ids = move_obj.search(cr, uid, [('inventory_line_id','=',id)], context=context)
            move_inf = move_obj.read(cr, uid, move_ids, ['product_id', 'product_unit_cost', 'product_uom', 'product_qty', 'location_id', 'location_dest_id'], context=context)
            line_loc = self.read(cr, uid, id, ['location_id'], context=context)['location_id'][0]
            total = 0.0
            for inf in move_inf:
                prc = inf['product_unit_cost']
                uom = inf['product_uom'][0]
                qty = inf['product_qty']
                src = inf['location_id'][0]
                dst = inf['location_dest_id'][0]
                prd = prod_obj.browse(cr, uid, inf['product_id'][0], context=context)
                net_prc = uom_obj._compute_price(cr, uid, uom, prc * qty, prd.uom_id.id)

                # Add or subtract from total, depending on whether
                # this move is to or away from the location specified
                # on the inventory line.
                if line_loc == dst:
                    total += net_prc
                elif line_loc == src:
                    total -= net_prc

            res[id] = total
        return res

    _columns = {
            'financial_impact' : fields.function(_calc_financial_impact, type='float', string='Financial Impact', help='Change in total value of stock.'),
    }

stock_inventory_line()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
