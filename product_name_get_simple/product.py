# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2014 credativ Ltd (<http://credativ.co.uk>).
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

from openerp.osv import osv

class Product(osv.Model):
    _inherit = 'product.product'

    def name_get(self, cr, uid, ids, context=None):
        """
        Return the product name.

        :param dict context: the ``product_display_format`` key can be used to
                             select a shorter version:
                                 - ``'code'``: return just ``default_code``
                                 - ``'name'``: return just the ``name`` field
                                 - ``'default'``: use the default name_get()
        """
        if context is None:
            context = {}
        if isinstance(ids, (int, long)):
            ids = [ids]

        display_format = context.get('product_display_format', 'default')

        if display_format == 'name':
            return [ (record['id'], record[display_format])
                    for record in self.read(cr, uid, ids, [display_format], context=context) ]
        elif display_format == 'code':
            return [ (record['id'], record.get('default_code') or record.get('name'))
                    for record in self.read(cr, uid, ids, ['default_code', 'name'], context=context) ]
        else:
            return super(Product, self).name_get(cr, uid, ids, context=context)
