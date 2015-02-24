# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2014 credativ Ltd (<http://credativ.co.uk>).
#    All Rights Reserved
#    $Id$
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

from openerp.osv import fields, osv

class sale_shop(osv.osv):
    _inherit='sale.shop'

    _columns = {
        'sale_prefix': fields.char('Sale Prefix', size=64, help="Appears at the start of sale order names for this shop."),
    }

sale_shop()

class sale_order(osv.osv):
    _inherit='sale.order'

    def create(self, cr, uid, vals, context=None):
        if vals.get('name','/')=='/':
            shop = self.pool.get('sale.shop').browse(cr, uid, vals.get('shop_id', []), context=context)
            prefix = shop and shop.sale_prefix or ''
            sequence = self.pool.get('ir.sequence').get(cr, uid, 'sale.order') or '/'
            vals['name'] = '%s%s' % (prefix, sequence)
        order =  super(sale_order, self).create(cr, uid, vals, context=context)
        return order

    def copy(self, cr, uid, id, default=None, context=None):
        """ base method override to change SO name"""

        #Can't set name in default as it been updated by sequence call in base method
        copy_id = super(sale_order,self).copy(cr,uid,id,default=default,context=context)
        vals = {}
        shop = self.browse(cr,uid,id,context).shop_id or False
        prefix = shop and shop.sale_prefix or ''
        sequence = self.pool.get('ir.sequence').get(cr, uid, 'sale.order') or '/'
        vals['name'] = '%s%s' % (prefix, sequence)
        self.write(cr,uid,copy_id,vals,context=context)
        return copy_id

sale_order()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
