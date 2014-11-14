from osv import fields, osv

class SaleOrder(osv.Model):

    _name    = 'sale.order'
    _inherit = 'sale.order'

    def test_no_value(self, cr, uid, ids, context=None, *args):
        ids = isinstance(ids, list) and ids or[ids]
        sale_line_obj = self.pool.get('sale.order.line')
        line_ids = sale_line_obj.search(cr, uid, [('order_id','in',ids)], context=context)
        line_values = sale_line_obj.read(cr, uid, line_ids, ['price_unit'], context=context)
        for lv in line_values:
            if lv['price_unit']:
                return False
        return True

    def _prepare_order_picking(self, cr, uid, order, context=None):
        res = super(SaleOrder, self)._prepare_order_picking(cr, uid, order, context=context)
        if self.test_no_value(cr, uid, order.id, context=context):
            res.update({'invoice_state' : 'none'})
        return res
