# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2014 credativ Ltd (<http://credativ.co.uk>).
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

import report

class account_voucher_remittance_report(report.report_sxw.rml_parse):
    _name = 'report.remittance.advice'

    def __init__(self, cr, uid, name, context=None):
        super(account_voucher_remittance_report, self).__init__(cr, uid, name, context=context)
        self.context = context
        self.localcontext.update({
            '_get_non_zero_lines': self._get_non_zero_lines,
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
        sum_amount_string = '%.2f' % (sum_amount)
        self.localcontext.update({
            '_get_sum_amount': sum_amount_string,
        })
        return sum_amount
        
report.report_sxw.report_sxw('report.remittance.advice', 'account.voucher', 'account_voucher_remittance_report/account_voucher_remittance_report.rml', parser=account_voucher_remittance_report, header=True)
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
