# -*- coding: utf-8 -*-
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

from openerp import api, models, fields, _

class mrp_bom(models.Model):
    _inherit = 'mrp.bom'

    minimum_qty = fields.Float('Minimum Qty', help="Minimum manufacturing quantity for this BoM")

class mrp_production(models.Model):
    _inherit = 'mrp.production'

    procurement_ids = fields.One2many('procurement.order', 'production_id', 'Procurements', copy=False, readonly=True)

    def _make_production_produce_line(self, cr, uid, production, context=None):
        stock_move = self.pool.get('stock.move')
        proc_obj = self.pool.get('procurement.order')
        source_location_id = production.product_id.property_stock_production.id
        destination_location_id = production.location_dest_id.id
        procs = proc_obj.search(cr, uid, [('production_id', '=', production.id)], context=context)
        procurements = procs and\
            proc_obj.browse(cr, uid, procs, context=context) or [False]
        for procurement in procurements:
            date_planned = procurement and proc_obj._get_date_planned(cr, uid, procurement, context=context) or production.date_planned
            data = {
                'name': production.name,
                'date': date_planned,
                'product_id': production.product_id.id,
                'product_uom': procurement and procurement.product_uom.id or production.product_uom.id,
                'product_uom_qty': procurement and procurement.product_qty or production.product_qty,
                'product_uos_qty': (procurement and procurement.product_uos and procurement.product_uos_qty) \
                                    or (production.product_uos and production.product_uos_qty) \
                                    or False,
                'product_uos': (procurement and procurement.product_uos and procurement.product_uos.id) \
                                or (production.product_uos and production.product_uos.id) \
                                or False,
                'location_id': source_location_id,
                'location_dest_id': destination_location_id,
                'move_dest_id': (procurement and procurement.move_dest_id and procurement.move_dest_id.id) or production.move_prod_id.id,
                'procurement_id': procurement and procurement.id,
                'company_id': production.company_id.id,
                'production_id': production.id,
                'origin': production.name,
                'group_id': procurement and procurement.group_id.id,
            }
            move_id = stock_move.create(cr, uid, data, context=context)
            stock_move.action_confirm(cr, uid, [move_id], context=context)
