# -*- coding: utf-8 -*-
# (c) 2016 credativ ltd. - Ondřej Kuzník
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import api, models


class ProcurementOrder(models.Model):
    _inherit = "procurement.order"

    def _merge_sensitive_fields(self):
        return super(ProcurementOrder, self)._merge_sensitive_fields() + [
            'sale_line_id',
        ]

    def _quiet_unlink(self):
        self.write({'sale_line_id': False})
        return super(ProcurementOrder, self)._quiet_unlink()
