# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution   
#    Copyright (C) 2012 credativ Ltd (<http://credativ.co.uk>).
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

import netsvc
import time
from osv import osv, fields
from tools.translate import _

class damagelog_osv(object):
    def create_damagelog(self, cr, uid, ids, context=None):
        rec_id = context and context.get('active_id', False)
        assert rec_id, _('Active ID is not set in Context')
        for data in self.browse(cr, uid, ids, context=context):
            move = self.pool.get('stock.move').browse(cr, uid, data.stock_move_id.id, context=context)
            if not move:
                raise osv.except_osv(_('UserError'), _('A valid stock move must be selected'))
            product_supplier = move.product_id.seller_ids and move.product_id.seller_ids[0].name.id or False 
            damagelog_id = self.pool.get('sale.damagelog').create(cr,uid,{'stock_move_id':data.stock_move_id.id,'product_qty':move.product_qty, 'product_uom':move.product_uom.id, 'product_supplier':product_supplier},context=context)
        return {
                'name': 'Damage Log',
                'view_type': 'form',
                'view_mode': 'form,tree',
                'res_model': 'sale.damagelog',
                'view_id': False,
                'res_id': damagelog_id,
                'type': 'ir.actions.act_window',
                }

class sale_create_damagelog_from_product(damagelog_osv, osv.osv_memory):
    _name = "sale.create.damagelog.from.product"
    _description = "Create Damage Log From Product"
    _columns = {
        'stock_move_id' : fields.many2one('stock.move', 'Stock Move', domain=[('product_id','=','product_id')], required=True),
        'product_id' : fields.many2one('product.product', 'Product'),
    }

    def default_get(self, cr, uid, fields, context):
        res = super(sale_create_damagelog_from_product, self).default_get(cr, uid, fields, context=context)
        res.update({'product_id': context and context.get('active_id', False) or False})
        return res

sale_create_damagelog_from_product()

class sale_create_damagelog_from_outgoing(damagelog_osv, osv.osv_memory):
    _name = "sale.create.damagelog.from.outgoing"
    _description = "Create Damage Log From Packing"
    _columns = {
        'stock_move_id' : fields.many2one('stock.move', 'Stock Move', domain=[('picking_id','=','picking_id')], required=True),
        'picking_id' : fields.many2one('stock.picking', 'Picking'),
    }

    def default_get(self, cr, uid, fields, context):
        res = super(sale_create_damagelog_from_outgoing, self).default_get(cr, uid, fields, context=context)
        res.update({'picking_id': context and context.get('active_id', False) or False})
        return res

sale_create_damagelog_from_outgoing()

class sale_create_damagelog_from_saleorder(damagelog_osv, osv.osv_memory):
    _name = "sale.create.damagelog.from.saleorder"
    _description = "Create Damage Log From Sale Order"
    _columns = {
        'stock_move_id' : fields.many2one('stock.move', 'Stock Move', domain=[('sale_line_id.order_id','=','sale_order_id')], required=True),
        'sale_order_id' : fields.many2one('sale.order', 'Sale Order'),
    }

    def default_get(self, cr, uid, fields, context):
        res = super(sale_create_damagelog_from_saleorder, self).default_get(cr, uid, fields, context=context)
        res.update({'sale_order_id': context and context.get('active_id', False) or False})
        return res

sale_create_damagelog_from_saleorder()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

