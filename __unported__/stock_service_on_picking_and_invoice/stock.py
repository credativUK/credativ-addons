# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution   
#    Copyright (C) 2014 credativ ltd (<http://www.credativ.co.uk>). All Rights Reserved
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

from osv import osv, fields

class StockPickingOut(osv.osv):
    _inherit = 'stock.picking.out'

    def _get_service_from_so(self, cr, uid, ids, field_name, arg, context=None):
        result = {}
        for record in self.browse(cr, uid, ids, context=context):
            if record.sale_id:
                result[record.id] = [x.id for x in record.sale_id.order_line if x.product_id and x.product_id.type == 'service']
        return result

    _columns = {
        'sale_service_line_ids': fields.function(_get_service_from_so, type='many2many', relation='sale.order.line', string='Services', readonly=True),
    }

class StockPicking(osv.osv):
    _inherit = 'stock.picking'

    def _get_service_from_so(self, cr, uid, ids, field_name, arg, context=None):
        result = {}
        for record in self.browse(cr, uid, ids, context=context):
            if record.sale_id:
                result[record.id] = [x.id for x in record.sale_id.order_line if x.product_id and x.product_id.type == 'service']
        return result

    _columns = {
        'sale_service_line_ids': fields.function(_get_service_from_so, type='many2many', relation='sale.order.line', string='Services', readonly=True),
    }

    def _invoice_hook(self, cr, uid, picking, invoice_id):
        invoice_line_obj = self.pool.get('account.invoice.line')
        res = super(StockPicking, self)._invoice_hook(cr, uid, picking, invoice_id)
        if picking.type == "out":
            for sale_line in picking.sale_service_line_ids:
                invoice_line_id = sale_line.invoice_line_create()
                invoice_line_obj.write(cr, uid, invoice_line_id, {'invoice_id': invoice_id})
        return res

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
