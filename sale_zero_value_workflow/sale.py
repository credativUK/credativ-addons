from osv import fields, osv

class SaleOrder(osv.Model):

    _name    = 'sale.order'
    _inherit = 'sale.order'

    def test_no_value(self, cr, uid, ids, *args):
        sale_line_obj = self.pool.get('sale.order.line')
        line_ids = sale_line_obj.search(cr, uid, [('order_id','in',ids)])
        line_values = sale_line_obj.read(cr, uid, line_ids, ['price_unit'])
        for lv in line_values:
            if lv['price_unit']:
                return False
        return True
