# -*- coding: utf-8 -*-
# Copyright (C) 2016 credativ Ltd (<http://credativ.co.uk>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import time

from openerp.osv import osv
from openerp.report import report_sxw
from openerp.tools.translate import _
from openerp.addons.account.report.common_report_header import common_report_header

PAYSQL = "SELECT inv_move_line.tax_amount AS tax_amount,\
                        inv_move_line.debit AS debit,\
                        inv_move_line.credit AS credit,\
                        inv_move_line.date AS date,\
                        inv_move_line.name AS line_name,\
                        inv_move_line.ref AS line_ref,\
                        move.name AS move_name,\
                        move.id AS move_id,\
                        account.id AS account_id,\
                        account.name AS account,\
                        account.code AS code,\
                        inv_move_line.tax_code_id,\
                        invoice.number, \
                        invoice.date_invoice, \
                        inv_move_line.credit - inv_move_line.debit as amount, \
                        invoice.reference, \
                        partner.name as partner \
                    FROM \
                        account_period AS period,\
                        account_invoice AS invoice,\
                        account_account AS account,\
                        res_partner AS partner,\
                        account_move AS move,\
                        account_move_line AS line\
                            JOIN account_move_line AS inv_rec_line\
                                ON line.reconcile_id = inv_rec_line.reconcile_id\
                                 AND line.id != inv_rec_line.id\
                            JOIN account_move_line AS inv_move_line\
                                ON inv_rec_line.move_id = inv_move_line.move_id\
                                 AND line.id != inv_move_line.id\
                            LEFT JOIN account_invoice AS noinv\
                                ON line.move_id = noinv.move_id\
                            LEFT JOIN account_move_line AS later_ml\
                                ON line.reconcile_id = later_ml.reconcile_id\
                                 AND line.id != later_ml.id\
                                 AND inv_move_line.id != later_ml.id\
                                 AND line.date <= later_ml.date\
                    WHERE line.state <> 'draft'\
                        AND inv_move_line.tax_code_id = %s\
                        AND inv_move_line.account_id = account.id\
                        AND account.company_id = %s\
                        AND invoice.move_id = inv_move_line.move_id\
                        AND inv_rec_line.account_id = invoice.account_id\
                        AND move.id = inv_move_line.move_id\
                        AND inv_move_line.partner_id = partner.id\
                        AND line.period_id = period.id\
                        AND line.period_id IN %s\
                        AND noinv.id IS NULL\
                        AND later_ml.id IS NULL\
                    ORDER BY account.id,account.code,inv_move_line.date, \
                             move.id, inv_move_line.tax_code_id"
INVSQL = "SELECT \
            inv.number, \
            inv.date_invoice, \
            SUM(aml.credit - aml.debit) as amount, \
            act.code, \
            act.name as account, \
            inv.reference, \
            part.name as partner \
        FROM account_move_line aml \
        INNER JOIN account_invoice inv \
            ON aml.move_id = inv.move_id \
        INNER JOIN account_account act \
            ON aml.account_id = act.id \
        LEFT JOIN res_partner part \
            ON inv.partner_id = part.id \
        WHERE (aml.credit > 0 OR aml.debit > 0) \
            AND aml.tax_code_id = %s \
            AND act.company_id = %s \
            AND aml.state != 'draft' \
            AND aml.period_id IN %s \
        GROUP BY aml.move_id,inv.number,aml.date,inv.date_invoice,act.code, \
                 act.name,inv.reference,part.name \
        ORDER BY aml.date"


class vat_report(report_sxw.rml_parse, common_report_header):

    def set_context(self, objects, data, ids, report_type=None):
        new_ids = ids
        self.period_ids = []
        period_obj = self.pool.get('account.period')
        self.display_detail = data['form']['display_detail']
        self.fiscalyear_id = data['form'].get('fiscalyear_id', False)

        if data['form'].get('period_from', False) and data['form'].get('period_to', False):
            self.period_ids = period_obj.build_ctx_periods(self.cr, self.uid, data['form']['period_from'], data['form']['period_to'])
        else:
            if not self.fiscalyear_id:
                self.cr.execute("select id from account_fiscalyear")
                self.fiscalyear_id = self.cr.fetchall()[0][0]
            self.period_ids = period_obj.search(self.cr, self.uid, [('fiscalyear_id', '=', self.fiscalyear_id)])
        return super(vat_report, self).set_context(objects, data, new_ids, report_type=report_type)

    def __init__(self, cr, uid, name, context=None):
        super(vat_report, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'time': time,
            'get_general': self._get_general,
            'get_currency': self._get_currency,
            'get_lines': self._get_lines,
            'get_fiscalyear': self._get_fiscalyear,
            'get_account': self._get_account,
            'get_start_period': self.get_start_period,
            'get_end_period': self.get_end_period,
            'get_basedon': self._get_basedon,
            'get_account_move_lines': self._get_account_move_lines,
            'get_tax_code_total': self._get_tax_code_total,
            'get_tax_code_name': self._get_tax_code_name,
        })

    def _get_basedon(self, form):
        based_on = form['form']['based_on']
        if based_on == 'invoices':
            return _('Invoices')
        elif based_on == 'payments':
            return _('Payments')

    def _get_account(self, data):
        if data.get('form', False) and data['form'].get('chart_account_id', False):
            return self.pool.get('account.account').browse(self.cr, self.uid, data['form']['chart_account_id']).name
        return ''

    def _get_lines(self, based_on, company_id=False, parent=False, level=0, context=None):
        period_list = self.period_ids
        codes = self._get_codes(based_on, company_id, parent, level, period_list, context=context)
        res = self._add_codes(based_on, codes, period_list, context=context)

        i = 0
        top_result = []
        while i < len(res):

            res_dict = {
                'id': res[i][1].id,
                'code': res[i][1].code,
                'name': res[i][1].name,
                'debit': 0,
                'credit': 0,
                'tax_amount': res[i][1].sum_period,
                'type': 1,
                'level': res[i][0],
                'pos': 0
            }

            top_result.append(res_dict)
            i+=1

        return top_result

    def _get_general(self, tax_code_id, period_list, company_id, based_on, context=None):
        if not self.display_detail:
            return []
        res = []
        obj_account = self.pool.get('account.account')
        periods_ids = tuple(period_list)
        if based_on == 'payments':
            self.cr.execute('SELECT sum(inv_move_line.tax_amount) AS tax_amount, \
                        sum(inv_move_line.debit) AS debit, \
                        sum(inv_move_line.credit) AS credit, \
                        count(*) as count, \
                        inv_move_line.tax_code_id as id \
                    FROM \
                        account_period AS period, \
                        account_invoice AS invoice, \
                        account_account AS account, \
                        res_partner AS partner, \
                        account_move AS move, \
                        account_move_line AS line \
                            JOIN account_move_line AS inv_rec_line \
                                ON line.reconcile_id = inv_rec_line.reconcile_id \
                                 AND line.id != inv_rec_line.id \
                            JOIN account_move_line AS inv_move_line \
                                ON inv_rec_line.move_id = inv_move_line.move_id \
                                 AND line.id != inv_move_line.id \
                            LEFT JOIN account_invoice AS noinv \
                                ON line.move_id = noinv.move_id \
                            LEFT JOIN account_move_line AS later_ml \
                                ON line.reconcile_id = later_ml.reconcile_id \
                                 AND line.id != later_ml.id \
                                 AND inv_move_line.id != later_ml.id \
                                 AND line.date <= later_ml.date \
                    WHERE line.state <> %s \
                        AND inv_move_line.tax_code_id = %s \
                        AND inv_move_line.account_id = account.id \
                        AND account.company_id = %s \
                        AND invoice.move_id = inv_move_line.move_id \
                        AND inv_rec_line.account_id = invoice.account_id \
                        AND move.id = inv_move_line.move_id \
                        AND inv_move_line.partner_id = partner.id \
                        AND line.period_id = period.id \
                        AND line.period_id IN %s \
                        AND noinv.id IS NULL \
                        AND later_ml.id IS NULL \
                    GROUP BY account.id, account.name, account.code, \
                             inv_move_line.tax_code_id',
                            ('draft', tax_code_id, company_id, periods_ids, ))
        else:
            self.cr.execute('SELECT SUM(line.tax_amount) AS tax_amount, \
                        SUM(line.debit) AS debit, \
                        SUM(line.credit) AS credit, \
                        COUNT(*) AS count, \
                        account.id AS account_id, \
                        account.name AS name,  \
                        account.code AS code \
                    FROM account_move_line AS line, \
                        account_account AS account \
                    WHERE line.state <> %s \
                        AND line.tax_code_id = %s  \
                        AND line.account_id = account.id \
                        AND account.company_id = %s \
                        AND line.period_id IN %s\
                        AND account.active \
                    GROUP BY account.id,account.name,account.code',
                            ('draft', tax_code_id, company_id, periods_ids,))
        res = self.cr.dictfetchall()

        return res

    def _get_codes(self, based_on, company_id, parent=False, level=0, period_list=[], context=None):
        obj_tc = self.pool.get('account.tax.code')
        ids = obj_tc.search(self.cr, self.uid, [('parent_id','=',parent),('company_id','=',company_id)], order='sequence, id', context=context)

        res = []
        for code in obj_tc.browse(self.cr, self.uid, ids, {'based_on': based_on}):
            res.append(('.'*2*level, code))

            res += self._get_codes(based_on, company_id, code.id, level+1, context=context)
        return res

    def _add_codes(self, based_on, account_list=[], period_list=[], context=None):
        res = []
        obj_tc = self.pool.get('account.tax.code')
        for account in account_list:
            ids = obj_tc.search(self.cr, self.uid, [('id','=', account[1].id)], context=context)
            sum_tax_add = 0
            for period_ind in period_list:
                for code in obj_tc.browse(self.cr, self.uid, ids, {'period_id':period_ind,'based_on': based_on}):
                    sum_tax_add = sum_tax_add + code.sum_period

            code.sum_period = sum_tax_add

            res.append((account[0], code))
        return res

    def _get_currency(self, form, context=None):
        return self.pool.get('res.company').browse(self.cr, self.uid, form['company_id'], context=context).currency_id.name

    def _get_account_move_lines(self, tax_id, based_on, company_id=False,
                                context=None):

        cr = self.cr
        tax_code_total = 0.0
        ret = []

        sql = based_on == 'payments' and PAYSQL or INVSQL
        cr.execute(sql, [tax_id, company_id, tuple(self.period_ids)])
        result = cr.dictfetchall()

        for res in result:
            partner = res['partner']
            # [Fix] Partner name in capital distort texts on report
            if isinstance(partner, unicode) and partner.isupper():
                partner = str(partner).capitalize()

            res_dict = {
                    'invoice': res['number'],
                    'date': res['date_invoice'],
                    'amount': '%0.2f' % res['amount'],
                    'act_code': res['code'],
                    'account': res['account'],
                    'reference': res['reference'],
                    'partner': partner[:23],
            }
            ret.append(res_dict)
            tax_code_total += float(res['amount'])

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

    def _get_tax_code_name(self, tax_id, context=None):
        cr = self.cr
        uid = self.uid
        tax_obj = self.pool.get('account.tax.code')
        return tax_obj.browse(cr, uid, tax_id, context=context).name


class report_vat(osv.AbstractModel):
    _name = 'report.account_vat_report.vat_invoices'
    _inherit = 'report.abstract_report'
    _template = 'account_vat_report.report_vat'
    _wrapped_report_class = vat_report

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
