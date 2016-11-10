# -*- coding: utf-8 -*-
# (c) 2016 credativ ltd. - Ondřej Kuzník
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import api, models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    @api.model
    def action_picking_create(self):
        ProcurementOrder = self.env['procurement.order']
        fields = ProcurementOrder._merge_sensitive_fields()

        for order in self:
            for line in order.order_line:
                to_merge = {}
                for procurement in line.procurement_ids:
                    key = procurement.read(fields)[0]
                    key.pop('id')
                    key = frozenset({(k,v) for k,v in key.iteritems()})

                    grouped = to_merge.get(key, ProcurementOrder.browse())
                    to_merge[key] = grouped | procurement

                for key, procurements in to_merge.iteritems():
                    target = procurements[0]
                    if target.state != 'running':
                        continue
                    target._merge_orders(procurements - target)

        return super(PurchaseOrder, self).action_picking_create()
