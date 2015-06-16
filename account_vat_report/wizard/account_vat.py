# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 credativ ltd (<http://www.credativ.co.uk>).
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

import time
from osv import osv, fields

class account_vat_invoices(osv.osv_memory):
    _name = 'account.vat.invoices'
    _description = 'Account Vat Invoices'
    _columns = {
        'based_on': fields.selection([('invoices', 'Invoices'),
                                      ('payments', 'Payments'),
                                      ('all', 'Posting')],
                                     'Based on', required=True),
        'chart_tax_id': fields.many2one('account.tax.code',
                                        'Chart of Tax',
                                        help='Select Charts of Taxes',
                                        domain=[('parent_id', '=', False)]),
        'chart_account_id': fields.many2one('account.account',
                                            'Chart of Account',
                                            help='Select Charts of Accounts',
                                            domain=[('parent_id', '=', False)]
                                            ),
        'company_id': fields.related('chart_account_id',
                                     'company_id',
                                     type='many2one',
                                     relation='res.company',
                                     string='Company',),
        'fiscalyear_id': fields.many2one('account.fiscalyear',
                                         'Fiscal Year',
                                         help='Keep empty for all open fiscal year'),
        'period_from': fields.many2one('account.period', 'Start Period'),
        'period_to': fields.many2one('account.period', 'End Period'),
        'date_from': fields.date("Start Date"),
        'date_to': fields.date("End Date"),
        'target_move': fields.selection([('posted', 'All Posted Entries'),
                                         ('all', 'All Entries')],
                                        'Target Moves'),
    }

    def _get_tax(self, cr, uid, context=None):
        taxes = self.pool.get('account.tax.code').search(cr,
                                                         uid,
                                                         [('parent_id', '=', False)],
                                                         limit=1)
        return taxes and taxes[0] or False

    def _get_fiscalyear(self, cr, uid, context=None):
        now = time.strftime('%Y-%m-%d')
        fiscalyears = self.pool.get('account.fiscalyear').search(cr, uid,
                                                    [('date_start', '<', now),
                                                     ('date_stop', '>', now)],
                                                    limit=1)
        return fiscalyears and fiscalyears[0] or False

    _defaults = {
        'based_on': 'invoices',
        'chart_tax_id': _get_tax,
        'fiscalyear_id': _get_fiscalyear,
        'target_move': 'all',
    }

    def create_vat(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        datas = {'ids': context.get('active_ids', [])}
        datas['model'] = 'account.tax.code'
        datas['form'] = self.read(cr, uid, ids, context=context)[0]
        for field in datas['form'].keys():
            if isinstance(datas['form'][field], tuple):
                datas['form'][field] = datas['form'][field][0]
        datas['form']['company_id'] = self.pool.get('account.tax.code').browse(cr, uid, [datas['form']['chart_tax_id']], context=context)[0].company_id.id
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'account.vat.invoices',
            'datas': datas,
            'header': False,
        }

account_vat_invoices()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
