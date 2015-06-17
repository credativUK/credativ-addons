# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 credativ ltd (<http://www.credativ.co.uk>). All Rights Reserved
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
from openerp.tools.translate import _
import netsvc

class SaleOrder(osv.Model):
    _inherit = 'sale.order'

    def _get_procurement_ids(self, cr, uid, ids, field_name, arg, context=None):
        proc_obj = self.pool.get('procurement.order')
        result = {}
        for id in ids:
            proc_ids = proc_obj.search(cr, uid, [('move_id.sale_line_id.order_id', '=', id)])
            result[id] = proc_ids
        return result

    _columns = {
            'procurement_ids': fields.function(_get_procurement_ids, type='one2many', relation='procurement.order', string='Procurements', readonly=True, copy=False),
        }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
