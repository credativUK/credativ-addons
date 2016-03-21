# -*- coding: utf-8 -*-
# Copyright (C) 2016 credativ Ltd (<http://credativ.co.uk>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api, _


class account_vat_invoices(models.TransientModel):
    _name = 'account.vat.invoices'
    _description = 'Account Vat Invoices'

    def _get_tax(self):
        taxes = self.env['account.tax.code'].search([('parent_id', '=', False)
                                                     ], limit=1)
        return taxes and taxes[0] or False

    def _get_fiscalyear(self):
        # Take tz date rather than system date
        now = fields.Date.context_today(self)
        return self.env['account.fiscalyear'].find(dt=now, exception=True)

    based_on = fields.Selection([('invoices', _('Invoices')),
                                 ('payments', _('Payments')),
                                 ], default='payments', required=True)
    chart_tax_id = fields.Many2one(comodel_name='account.tax.code',
                                   default=_get_tax,
                                   string=_('Chart of Tax'),
                                   help=_('Select Charts of Taxes'),
                                   domain=[('parent_id', '=', False)])
    display_detail = fields.Boolean(default=True)
    chart_account_id = fields.Many2one(comodel_name='account.account',
                                       string=_('Chart of Account'),
                                       help=_('Select Charts of Accounts'),
                                       domain=[('parent_id', '=', False)])
    company_id = fields.Many2one(related=_('chart_tax_id.company_id'))
    fiscalyear_id = fields.Many2one(comodel_name='account.fiscalyear',
                                    default=_get_fiscalyear,
                                    string=_('Fiscal Year'),
                                    help=_('Keep empty for all open year'))
    period_from = fields.Many2one(comodel_name='account.period',
                                  string=_('Start Period'))
    period_to = fields.Many2one(comodel_name='account.period',
                                string=_('End Period'))
    date_from = fields.Date(string=_("Start Date"))
    date_to = fields.Date(string=_("End Date"))
    target_move = fields.Selection([('posted', _('All Posted Entries')),
                                    ('all', _('All Entries')),
                                    ])

    @api.multi
    def create_vat(self):
        datas = {'ids': self._context.get('active_ids', [])}
        datas['model'] = 'account.tax.code'
        datas['form'] = self.read()[0]
        for field in datas['form'].keys():
            if isinstance(datas['form'][field], tuple):
                datas['form'][field] = datas['form'][field][0]
        return self.env['report'].get_action(self,
                                             'account_vat_report.vat_invoices',
                                             data=datas)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
