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

from openerp import api, fields, models

class StockPickingLabelsItems(models.TransientModel):
    _name = 'wizard.stock.picking.labels.items'

    wizard_id = fields.Many2one('wizard.stock.picking.labels', required=True)
    product_id = fields.Many2one('product.product', string="Product", required=True)
    quantity = fields.Integer("Label count")

class StockPickingLabels(models.TransientModel):
    _name = 'wizard.stock.picking.labels'

    item_ids = fields.One2many('wizard.stock.picking.labels.items', 'wizard_id')

    @api.model
    def default_get(self, fields):
        res = super(StockPickingLabels, self).default_get(fields)
        context = self.env.context
        picking_ids = context.get('active_ids', [])
        active_model = context.get('active_model')

        if not picking_ids or len(picking_ids) != 1:
            # Partial Picking Processing may only be done for one picking at a time
            return res
        assert active_model in ('stock.picking'), 'Bad context propagation'
        picking_id, = picking_ids
        picking = self.env['stock.picking'].browse(picking_id)

        items = []
        for line in picking.move_lines:
            item = {
                'product_id': line.product_id.id,
                'quantity': line.product_qty,
            }
            items.append(item)

        res.update(item_ids=items)
        return res

    @api.multi
    def print_labels(self):
        '''This function prints the labels'''
        return self.env["report"].get_action(self, 'stock_picking_barcode_labels.report_picking_product_labels')
