# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution	
#    Copyright (C) 2012 credativ ltd (<http://www.credativ.co.uk>). All Rights Reserved
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

from osv import fields,osv

class report_stock_levels(osv.osv):
    _name = "report.stock.levels"
    _description = "Current stock levels for locations"
    _auto = False
    _columns = {
            'location_id': fields.many2one('stock.location', 'Stock Location', readonly=True, select=True),
            'product_id': fields.many2one('product.product', 'Product', readonly=True, select=True),
            'real': fields.float('Current Stock', readonly=True),
            'product_uom': fields.many2one('product.uom', 'Unit of Measure', readonly=True)
            }
    def init(self, cr):
        cr.execute("DROP VIEW IF EXISTS report_stock_levels")
        cr.execute("""
            create or replace view report_stock_levels as (
                SELECT
                        MAX(inout.id) AS id,
                        SUM(product_qty) as real,
                        inout.location as location_id,
                        product_id,
                        product_uom
                FROM
                        product_template p LEFT JOIN
                        (SELECT id*2+1 as id, location_dest_id as location, product_id, product_uom, product_qty
                        FROM stock_move WHERE state='done'
                        UNION ALL
                        SELECT id*2 as id, location_id as location, product_id, product_uom, -product_qty
                        FROM stock_move WHERE state='done'
                        ) inout ON p.type='product' AND p.id=inout.product_id
                GROUP BY inout.location, product_id, product_uom
                HAVING SUM(product_qty) <> 0.0
            )
        """)
report_stock_levels()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
