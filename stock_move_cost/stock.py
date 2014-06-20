from osv import osv, fields



class stock_move(osv.osv):
    _name = 'stock.move'
    _inherit = 'stock.move'


    _columns = {
            'product_unit_cost' : fields.float('Unit Cost', help="The product's unit cost at the time of this move's creation.", readonly=True)
    }


    _defaults = {
            'product_unit_cost' : 0.0,
    }



    def _get_product_cost(self, cr, uid, ids, prod_id, *args, **kwargs):
        values = {'product_unit_cost' : 0.0}
        if prod_id:
            prod_obj = self.pool.get('product.product')
            prod_inf = prod_obj.read(cr, uid, prod_id, ['standard_price'], context=kwargs.get('context'))
            prod_cst = prod_inf['standard_price']
            if prod_cst:
                values.update({'product_unit_cost' : prod_cst})
        return values


    def onchange_product_id(self, *args, **kwargs):
        res = super(stock_move, self).onchange_product_id(*args, **kwargs)
        if not res.get('value'):
            res.update({'value' : {}})
        res['value'].update(self._get_product_cost(*args, **kwargs))
        return res


    def write(self, cr, uid, ids, values, context=None):
        prod_id  = values.get('product_id', False)
        if prod_id:
            cost_val = self._get_product_cost(cr, uid, ids, prod_id, context=context)
            values.update(cost_val)
        return super(stock_move, self).write(cr, uid, ids, values, context=context)


    def create(self, cr, uid, values, context=None):
        prod_id  = values.get('product_id' , False)
        cost_val = self._get_product_cost(cr, uid, [], prod_id, context=context)
        values.update(cost_val)
        return super(stock_move, self).create(cr, uid, values, context=context)



stock_move()
