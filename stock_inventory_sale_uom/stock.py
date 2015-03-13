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

from openerp.osv import osv

class stock_inventory_line(osv.osv):
    _inherit = "stock.inventory.line"

    def on_change_product_id(self, cr, uid, ids, location_id, product, uom=False, to_date=False):
        """ Changes UoM to match UoS if product_id changes.
        @param location_id: Location id
        @param product: Changed product_id
        @param uom: UoM product
        @return:  Dictionary of changed values
        """
        res = super(stock_inventory_line, self).on_change_product_id(cr, uid, ids, location_id, product, uom, to_date)
        if res.get('value', False) and res['value'].get('product_uom', False):
            obj_product = self.pool.get('product.product').browse(cr, uid, product)
            res['value']['product_uom'] = obj_product.uos_id.id
        return res

stock_inventory_line()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
