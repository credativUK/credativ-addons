# -*- coding: utf-8 -*-

from openerp import api, fields, models


class ProcurementOrder(models.Model):
    _inherit = 'procurement.order'

    lot_id = fields.Many2one('stock.production.lot')

    @api.model
    def _run_move_create(self, procurement):
        vals = super(ProcurementOrder, self)._run_move_create(procurement)
        if procurement.lot_id:
            vals.update({'restrict_lot_id': procurement.lot_id.id})
        return vals
