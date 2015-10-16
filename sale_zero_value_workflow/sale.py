from osv import fields, osv


class SaleOrder(osv.Model):

    _name = 'sale.order'
    _inherit = 'sale.order'

    def test_no_value(self, cr, uid, ids, context=None, *args):
        ids = isinstance(ids, list) and ids or[ids]
        line_obj = self.pool.get('sale.order.line')
        domain = [('order_id', 'in', ids)]
        line_ids = line_obj.search(cr, uid, domain, context=context)
        fields = ['price_unit']
        line_vals = line_obj.read(cr, uid, line_ids, fields, context=context)
        for lv in line_vals:
            if lv['price_unit']:
                return False
        return True

    def _prepare_order_picking(self, cr, uid, order, context=None):
        parent = super(SaleOrder, self)
        res = parent._prepare_order_picking(cr, uid, order, context=context)
        if self.test_no_value(cr, uid, order.id, context=context):
            res.update({'invoice_state': 'none'})
        return res
