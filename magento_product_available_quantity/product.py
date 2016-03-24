# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2016 credativ Ltd (<http://credativ.co.uk>).
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

from openerp.osv import orm


class product_template(orm.Model):
    _inherit = 'product.template'

    def write(self, cr, uid, ids, vals, context=None):
        res = super(product_template, self).write(cr, uid, ids, vals, context=context)
        if 'state' in vals:
            prod_obj = self.pool.get('product.product')
            mag_prod_obj = self.pool.get('magento.product.product')
            isinstance(ids, list) and ids or [ids]
            prod_ids = prod_obj.search(cr, uid, [('product_tmpl_id', 'in', ids)], context=context)
            prod_bindings = prod_obj.read(cr, uid, prod_ids, ['magento_bind_ids'], context=context)
            mag_prod_ids = reduce(list.__add__, [p['magento_bind_ids'] for p in prod_bindings], [])
            mag_prod_obj.recompute_magento_qty(cr, uid, mag_prod_ids, context=context)
        return res


class magento_product_product(orm.Model):
    _inherit = 'magento.product.product'

    def _recompute_magento_qty_backend(self, cr, uid, backend, products, read_fields=None, context=None):
        read_fields = read_fields or []
        if 'state' not in read_fields: read_fields.append('state')
        return super(magento_product_product, self)._recompute_magento_qty_backend(
                         cr, uid, backend, products, read_fields=read_fields, context=context)

    def _magento_qty(self, cr, uid, product, backend, location, stock_field, context=None):
        if product.get('state') in ['draft', 'obsolete']:
            return 0
        return super(magento_product_product, self)._magento_qty(
                         cr, uid, product, backend, location, stock_field, context=context)

