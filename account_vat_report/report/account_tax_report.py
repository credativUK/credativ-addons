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

from openerp.addons.account.report.common_report_header import common_report_header
from report import report_sxw
from tools.translate import _

class tax_report_invoices(report_sxw.rml_parse, common_report_header):

    _name = 'report.account.vat.invoices'

    def set_context(self, objects, data, ids, report_type=None):
        new_ids = ids
        res = {}
        self.period_ids = []
        period_obj = self.pool.get('account.period')
        res['periods'] = ''
        res['fiscalyear'] = data['form'].get('fiscalyear_id', False)
        if data['form'].get('period_from', False) and data['form'].get('period_to', False):
            self.period_ids = period_obj.build_ctx_periods(self.cr,
                                                self.uid,
                                                data['form']['period_from'],
                                                data['form']['period_to'])
            periods_l = period_obj.read(self.cr, self.uid, self.period_ids,
                                        ['name'])
            for period in periods_l:
                if res['periods'] == '':
                    res['periods'] = period['name']
                else:
                    res['periods'] += ", " + period['name']
        return super(tax_report_invoices, self).set_context(objects,
                                                            data,
                                                            new_ids,
                                                            report_type=report_type)

    def __init__(self, cr, uid, name, context=None):
        super(tax_report_invoices, self).__init__(cr, uid, name,
                                                  context=context)

        self.localcontext.update({
            'time': time,
            'get_codes': self._get_codes,
            'get_lines': self._get_lines,
            'get_fiscalyear': self._get_fiscalyear,
            'get_start_period': self.get_start_period,
            'get_end_period': self.get_end_period,
            'get_basedon': self._get_basedon,
            'get_account_move_lines': self._get_account_move_lines,
            'get_tax_code_total': self._get_tax_code_total,
            'get_vat_box_str': self._get_vat_box_str,
            'get_tax_code_name': self._get_tax_code_name,
            'get_date_limit': self._get_date_limit,
        })

    def _get_basedon(self, form):
        based_on = form['form']['based_on']
        if based_on == 'invoices':
            return _('Invoices')
        elif based_on == 'payments':
            return _('Payments')

    def _get_lines(self, based_on, company_id=False, parent=False, level=0,
                   context=None):
        period_list = self.period_ids
        res = self._get_codes(based_on, company_id, parent, level, period_list,
                              context=context)
        if period_list:
            res = self._add_codes(based_on, res, period_list, context=context)
        else:
            self.cr.execute("select id from account_fiscalyear")
            fy = self.cr.fetchall()
            self.cr.execute("select id from account_period where fiscalyear \
                _id = %s", (fy[0][0],))
            periods = self.cr.fetchall()
            for p in periods:
                period_list.append(p[0])
            res = self._add_codes(based_on, res, period_list, context=context)

        i = 0
        top_result = []
        for (tmp_str, tax) in res:

            res_dict = {
                'id': tax.id,
                'code': tax.code,
                'name': tax.name,
                'debit': 0,
                'credit': 0,
                'tax_amount': tax.sum_period,
                'type': 1,
                'level': tax,
                'pos': 0
            }

            top_result.append(res_dict)
        return top_result

    def _get_codes(self, based_on, company_id, parent=False, level=0,
                   period_list=[], context=None):
        obj_tc = self.pool.get('account.tax.code')
        ids = obj_tc.search(self.cr, self.uid,
                            [('parent_id', '=', parent),
                             ('company_id', '=', company_id)],
                            order='sequence', context=context)

        res = []
        for code in obj_tc.browse(self.cr, self.uid, ids,
                                  {'based_on': based_on}):
            res.append(('.'*2*level, code))

            res += self._get_codes(based_on, company_id, code.id, level+1,
                                   context=context)
        return res

    def _add_codes(self, based_on, account_list=[], period_list=[],
                   context=None):
        res = []
        obj_tc = self.pool.get('account.tax.code')
        for account in account_list:
            ids = obj_tc.search(self.cr, self.uid,
                                [('id', '=', account[1].id)],
                                context=context)
            sum_tax_add = 0
            for period_ind in period_list:
                for code in obj_tc.browse(self.cr, self.uid, ids,
                                          {'period_id': period_ind,
                                           'based_on': based_on}):

                    sum_tax_add = sum_tax_add + code.sum_period

            code.sum_period = sum_tax_add

            res.append((account[0], code))
        return res

    def _get_account_move_lines(self, tax_id, based_on, company_id=False,
                                context=None):
        cr = self.cr
        uid = self.uid
        date_from = date_to = False

        prd_obj = self.pool.get('account.period')
        fields = {
            'payments': ['inv.number', 'inv.date_invoice',
                         'SUM(aml.credit - aml.debit)', 'act.code', 'act.name',
                         'inv.reference', 'part.name as partner'],
            'invoices': ['inv.number', 'inv.date_invoice',
                         'SUM(aml.credit - aml.debit)', 'act.code', 'act.name',
                         'inv.reference', 'part.name as partner'],
            'all': ['aml.name', 'aml.date',
                    'SUM(aml.credit - aml.debit)', 'act.code', 'act.name',
                    'aml.ref', 'part.name as partner']
            }
        period_lst = str(self.period_ids).replace('[', '(').replace(']', ')')

        if based_on == 'all':
            sql = 'SELECT ' + ','.join(fields[based_on]) + ' ' \
                + 'FROM account_move_line aml ' \
                + 'INNER JOIN account_account act ' \
                + 'ON aml.account_id = act.id ' \
                + 'LEFT JOIN res_partner part ' \
                + 'ON aml.partner_id = part.id ' \
                + 'WHERE (aml.credit > 0 OR aml.debit > 0) ' \
                + 'AND aml.state != \'draft\' ' \
                + 'AND aml.period_id IN %s ' % period_lst

            extra_group_by = 'aml.name,aml.ref '
        else:
            sql = 'SELECT ' + ','.join(fields[based_on]) + ' ' \
                + 'FROM account_move_line aml ' \
                + 'INNER JOIN account_invoice inv ' \
                + 'ON aml.move_id = inv.move_id ' \
                + 'INNER JOIN account_account act ' \
                + 'ON aml.account_id = act.id ' \
                + 'LEFT JOIN res_partner part ' \
                + 'ON inv.partner_id = part.id ' \
                + 'WHERE (aml.credit > 0 OR aml.debit > 0) ' \
                + 'AND aml.state != \'draft\' ' \
                + 'AND aml.period_id IN %s ' % period_lst

            extra_group_by = 'inv.number,inv.date_invoice,inv.reference '

        if company_id:
            sql += 'AND act.company_id = %d ' % company_id

        if based_on == 'payments':
            sql += 'AND (inv.state = \'paid\' ' \
                + 'OR inv.id IS NULL) '

        sql += 'AND aml.tax_code_id = %s ' % tax_id
        sql += 'GROUP BY aml.move_id,' \
            + 'aml.date,act.code,' \
            + 'act.name,part.name,' + extra_group_by
        sql += 'ORDER BY aml.date'

        cr.execute(sql)
        result = cr.fetchall()

        tax_code_total = 0.0

        ret = []
        for res in result:
            assert len(res) == len(fields[based_on])
            partner = res[6]
            #[Fix] Partner name in capital distort texts on report
            if isinstance(res[6], unicode) and res[6].isupper():
                partner = str(res[6]).capitalize()

            res_dict = {
                'invoice': res[0],
                'date': res[1],
                'amount': '%0.2f' % res[2],
                'act_code': res[3],
                'account': res[4],
                'reference': res[5] and res[5].capitalize() or '',
                'partner': partner and partner[:24],
            }
            ret.append(res_dict)
            tax_code_total += float(res[2])

        if not self.localcontext.get('tax_code_totals'):
            self.localcontext.update({'tax_code_totals': {}})

        self.localcontext['tax_code_totals'].update({tax_id: tax_code_total})

        return ret

    def _get_tax_code_total(self, tax_id, context=None):
        totals = self.localcontext.get('tax_code_totals')
        total = 0.
        if totals:
            total = totals[tax_id]
        return '%0.2f' % total

    def _get_vat_box_str(self, tax_id, context=None):
        cr = self.cr
        uid = self.uid
        tax_obj = self.pool.get('account.tax.code')
        tax = tax_obj.browse(cr, uid, tax_id, context=context)
        return 'VAT Box %s' % tax.code

    def _get_tax_code_name(self, tax_id, context=None):
        cr = self.cr
        uid = self.uid
        tax_obj = self.pool.get('account.tax.code')
        return tax_obj.browse(cr, uid, tax_id, context=context).name

    def _get_date_limit(self, year, period, bound='low', context=None):
        cr = self.cr
        uid = self.uid
        pd_obj = self.pool.get('account.period')
        yr_obj = self.pool.get('account.fiscalyear')

        ret = ''
        field = (bound == 'high') and 'date_stop' or 'date_start'
        if period:
            ret = pd_obj.read(cr, uid, period, [field], context=context)[field]
        else:
            op = (bound == 'high') and 'MAX' or 'MIN'
            sql = 'SELECT ' + op + '(' + field + ') ' \
                + 'FROM account_period ' \
                + 'WHERE fiscalyear_id = %d' % year
            cr.execute(sql)
            res = cr.fetchall()
            if res and res[0]:
                ret = res[0][0]
        return ret

report_sxw.report_sxw('report.account.vat.invoices', 'account.tax.code',
                      'addons/account_vat_report/report/account_tax_report.rml',
                      parser=tax_report_invoices, header="internal")


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
