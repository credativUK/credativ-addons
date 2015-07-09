# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 credativ Ltd (<http://credativ.co.uk>).
#    All Rights Reserved
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

from openerp import api, models, fields

class StockPickingType(models.Model):
    _inherit = 'stock.picking.type'

    default_procure_method = fields.Selection(string='Default Supply Method', selection=[
        ('make_to_stock', 'Default: Take From Stock'),
        ('make_to_order', 'Advanced: Apply Procurement Rules'),
        ])

class StockMove(models.Model):
    _inherit = 'stock.move'

    def _default_procure_method(self, cr, uid, context=None):
        context = context or {}
        if context.get('default_picking_type_id', False):
            picking_type_id = self.pool.get('stock.picking.type').browse(
                cr, uid, context['default_picking_type_id'], context)
            if picking_type_id.default_procure_method:
                return picking_type_id.default_procure_method
        return 'make_to_stock'

    _defaults = {
        'procure_method': _default_procure_method,
    }
