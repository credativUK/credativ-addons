# -*- coding: utf-8 -*-
# © 2016 credativ Ltd (http://credativ.co.uk)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp.report import report_sxw
from openerp import models


class AccountVoucherRemittance(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context=None):
        super(AccountVoucherRemittance, self).\
            __init__(cr, uid, name, context=context)
        self.context = context
        self.sum_amount = 0.0
        self.localcontext.update({
            'get_non_zero_lines': self._get_non_zero_lines,
            'get_sum_amount': self._get_total,
            'get_currency': self._get_currency,
        })

    def _get_non_zero_lines(self, all_line_ids):
        filtered_line_ids = [x for x in all_line_ids if x.amount]
        self._get_sum_amount(filtered_line_ids)
        return filtered_line_ids

    def _get_sum_amount(self, filtered_line_ids):
        sum_amount = 0
        for line in filtered_line_ids:
            if line.type == 'cr':
                if line.account_id and line.account_id.type == 'payable':
                    sum_amount -= line.amount
                else:
                    sum_amount += line.amount
            else:
                if line.account_id and line.account_id.type == 'payable':
                    sum_amount += line.amount
                else:
                    sum_amount -= line.amount
        self.sum_amount = sum_amount
        return sum_amount

    def _get_total(self):
        return self.sum_amount

    def _get_currency(self, voucher):
        currency = voucher.journal_id.currency or \
            voucher.company_id.currency_id
        return currency


class ReportPrintDispatch(models.AbstractModel):
    _name = 'report.account_voucher_remittance_report.report_voucherremittance'
    _inherit = 'report.abstract_report'
    _template = 'account_voucher_remittance_report.report_voucherremittance'
    _wrapped_report_class = AccountVoucherRemittance
