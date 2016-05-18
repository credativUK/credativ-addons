# -*- coding: utf-8 -*-
#
#   See __openerp__.py about license
#

from openerp import api, fields, models
import openerp.addons.decimal_precision as dp


class SageTaxReport(models.TransientModel):
    _inherit = "account.vat.declaration"

    sage_tax_report = fields.Boolean('Sage Tax Report')

    @api.multi
    def create_vat(self):
        report = 'account.report_vat'
        if self.sage_tax_report:
            datas = {'ids': self._context.get('active_ids', [])}
            datas['model'] = 'account.tax.code'
            datas['form'] = self.read()[0]
            for field in datas['form'].keys():
                if isinstance(datas['form'][field], tuple):
                    datas['form'][field] = datas['form'][field][0]
            report = 'account_tax_sage_report.report_vat'
            return self.env['report'].get_action(self, report, data=datas)
        return super(SageTaxReport, self).create_vat()
