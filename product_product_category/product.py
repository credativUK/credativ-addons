from osv import osv, fields


class product_product(osv.osv):
    _name = 'product.product'
    _inherit = 'product.product'

    _columns = {
            'categ_id': fields.many2one('product.category','Category', required=True, change_default=True, domain="[('type','=','normal')]" ,help="Select category for the current product"),
    }


    def _default_category(self, cr, uid, context=None):
        tmpl_obj = self.pool.get('product.template')
        return tmpl_obj._default_category(cr, uid, context=context)


    _defaults = {
            'categ_id': _default_category,
    }
