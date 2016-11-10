# -*- coding: utf-8 -*-
# (c) 2016 credativ ltd. - Ondřej Kuzník
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import api, models


class ProcurementOrder(models.Model):
    _inherit = "procurement.order"

    def _merge_sensitive_fields(self):
        """A list of fields that should be the same for two procurements to be
        considered for merging"""
        return [
            'state',
            'company_id',
            'product_id',
            'rule_id',
            'group_id',
            'priority',
            'product_uom',
            'product_uos',
            'origin',
        ]

    def _quiet_unlink(self):
        """For removing procurements superseded by a merge"""
        # we don't actually want to cancel the procurement, just need this to
        # be able to unlink them
        self.write({'state': 'cancel'})
        self.unlink()

    def _prepare_merged_values(self):
        return {'product_qty': sum(self.mapped('product_qty')),
                'product_uos_qty': sum(self.mapped('product_uos_qty')),
                'date_planned': min(self.mapped('date_planned')),
        }

    @api.multi
    def _merge_orders(self, to_merge):
        """Merges procurements into self, then removes them from the system"""
        self.ensure_one()
        if self & to_merge:
            raise ValueError('Cannot merge procurement with itself!')
        if not to_merge:
            return self

        procurements = self | to_merge

        self.write(procurements._prepare_merged_values())
        to_merge._quiet_unlink()

        return self
