from osv import osv, fields

class stock_picking_out(osv.osv):

    _name    = 'stock.picking.out'
    _inherit = 'stock.picking.out'

    _columns = {
            'delivery_address' : fields.many2one('res.partner', 'Delivery Address', help='Address to which the products will be delivered.')
    }


stock_picking_out()
