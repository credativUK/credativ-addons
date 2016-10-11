# -*- coding: utf-8 -*-

from openerp import api, fields, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    lot_id = fields.Many2one('stock.production.lot',
                             domain="[('product_id', '=', product_id)]")

    @api.multi
    def _prepare_order_line_procurement(self, *args, **kwargs):
        self.ensure_one()
        vals = super(SaleOrderLine, self).\
            _prepare_order_line_procurement(*args, **kwargs)
        if self.lot_id:
            vals.update({'lot_id': self.lot_id.id})
        return vals
