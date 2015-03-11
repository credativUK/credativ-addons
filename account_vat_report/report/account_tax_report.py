# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright 2014 credativ Ltd
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
        self.display_detail = data['form']['display_detail']
        res['periods'] = ''
        res['fiscalyear'] = data['form'].get('fiscalyear_id', False)
        if data['form'].get('period_from', False) and data['form'].get('period_to', False):
            self.period_ids = period_obj.build_ctx_periods(self.cr, self.uid, data['form']['period_from'], data['form']['period_to'])
            periods_l = period_obj.read(self.cr, self.uid, self.period_ids, ['name'])
            for period in periods_l:
                if res['periods'] == '':
                    res['periods'] = period['name']
                else:
                    res['periods'] += ", "+ period['name']
        return super(tax_report_invoices, self).set_context(objects, data, new_ids, report_type=report_type)


    def __init__(self, cr, uid, name, context=None):
        super(tax_report_invoices, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'time': time,
            'get_codes': self._get_codes,
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


    def _get_account(self, data):
        if data.get('form', False) and data['form'].get('chart_account_id', False):
            return pooler.get_pool(self.cr.dbname).get('account.account').browse(self.cr, self.uid, data['form']['chart_account_id']).name
        return ''


    def _get_lines(self, based_on, company_id=False, parent=False, level=0, context=None):
        period_list = self.period_ids
        res = self._get_codes(based_on, company_id, parent, level, period_list, context=context)
        if period_list:
            res = self._add_codes(based_on, res, period_list, context=context)
        else:
            self.cr.execute ("select id from account_fiscalyear")
            fy = self.cr.fetchall()
            self.cr.execute ("select id from account_period where fiscalyear_id = %s",(fy[0][0],))
            periods = self.cr.fetchall()
            for p in periods:
                period_list.append(p[0])
            res = self._add_codes(based_on, res, period_list, context=context)

        i = 0
        top_result = []
        while i < len(res):

            res_dict = {
                'id' : res[i][1].id,
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
            res_general = self._get_general(res[i][1].id, period_list, company_id, based_on, context=context)
            ind_general = 0
            while ind_general < len(res_general):
                res_general[ind_general]['type'] = 2
                res_general[ind_general]['pos'] = 0
                res_general[ind_general]['level'] = res_dict['level']
                top_result.append(res_general[ind_general])
                ind_general+=1
            i+=1
        return top_result


    def _get_general(self, tax_code_id, period_list, company_id, based_on, context=None):
        if not self.display_detail:
            return []
        res = []
        obj_account = self.pool.get('account.account')
        periods_ids = tuple(period_list)

        if based_on == 'payments':
            self.cr.execute('SELECT inv_move_line.tax_amount AS tax_amount, \
                    inv_move_line.debit AS debit, \
                    inv_move_line.credit AS credit, \
                    COUNT(*) AS count, \
                    inv_move_line.date AS date, \
                    inv_move_line.name AS line_name, \
                    inv_move_line.ref AS line_ref, \
                    move.name AS move_name, \
                    move.id AS move_id, \
                    account.id AS account_id, \
                    account.name AS name,  \
                    account.code AS code, \
                    partner.name AS partner_name \
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
                GROUP BY \
                    inv_move_line.tax_amount, \
                    inv_move_line.debit, \
                    inv_move_line.credit, \
                    inv_move_line.date, \
                    inv_move_line.name, \
                    inv_move_line.ref, \
                    inv_move_line.reconcile_id,\
                    move.name,\
                    move.id,\
                    account.id,\
                    account.name,\
                    account.code,\
                    partner.name\
                ORDER BY account.id,account.code,inv_move_line.date, move.id',
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
                    GROUP BY account.id,account.name,account.code', ('draft', tax_code_id,
                        company_id, periods_ids,))
        res = self.cr.dictfetchall()

        i = 0
        while i<len(res):
            res[i]['account'] = obj_account.browse(self.cr, self.uid, res[i]['account_id'], context=context)
            i+=1
        return res


    def _get_codes(self, based_on, company_id, parent=False, level=0, period_list=[], context=None):
        obj_tc = self.pool.get('account.tax.code')
        ids = obj_tc.search(self.cr, self.uid, [('parent_id','=',parent),('company_id','=',company_id)], order='sequence', context=context)

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

    def _get_payment_line_query(self):
        ''' Get query string based on tax_id '''

        sql = 'SELECT invoice.number, \
                        invoice.date_invoice, \
                        (inv_move_line.credit - inv_move_line.debit), \
                        account.code AS code, \
                        account.name AS name, \
                        inv_move_line.ref AS line_ref, \
                        partner.name AS partner_name \
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
                    GROUP BY \
                        inv_move_line.tax_amount, \
                        inv_move_line.debit, \
                        inv_move_line.credit, \
                        invoice.number, \
                        invoice.date_invoice, \
                        account.code, \
                        account.name, \
                        inv_move_line.ref, \
                        partner.name, \
                        inv_move_line.name, \
                        move.name, \
                        move.id, \
                        account.id, \
                        inv_move_line.date \
                    ORDER BY account.id,account.code,inv_move_line.date, move.id'

        return sql

    def _get_account_move_lines(self, tax_id, based_on, company_id=False, context=None):
        cr  = self.cr
        uid = self.uid
        date_from = date_to = False

        prd_obj = self.pool.get('account.period')

        fields = [
                     'inv.number',
                     'inv.date_invoice',
                     'aml.tax_amount',
                     'act.code',
                     'act.name',
                     'inv.reference',
                     'part.name as partner',
                 ]

        period_lst = str(self.period_ids).replace('[','(').replace(']',')')

        if based_on == 'invoices':
            sql = 'SELECT ' + ','.join(fields) + ' ' \
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

            if company_id:
                sql += 'AND act.company_id = %d ' % company_id

            #if based_on == 'payments':
                #sql += 'AND (inv.state = \'paid\' ' \
                    #+ 'OR inv.id IS NULL) '

            sql += 'AND aml.tax_code_id = %s ' % tax_id
            sql += 'GROUP BY aml.move_id,inv.number,aml.date,inv.date_invoice,act.code,act.name,inv.reference,part.name,aml.tax_amount '
            sql += 'ORDER BY aml.date'
            cr.execute(sql)

        else:
            sql = self._get_payment_line_query()
            cr.execute(sql,('draft', tax_id,
                    company_id, tuple(self.period_ids), ))

        result = cr.fetchall()
        tax_code_total = 0.0

        ret = []
        for res in result:
            assert len(res) == len(fields)
            partner = res[6]
            #[Fix] Partner name in capital distort texts on report
            if isinstance(res[6],unicode) and res[6].isupper():
                partner = str(res[6]).capitalize()

            res_dict = {
                    'invoice'   : res[0],
                    'date'      : res[1],
                    'amount'    : '%0.2f' % res[2],
                    'act_code'  : res[3],
                    'account'   : res[4],
                    'reference' : res[5] and res[5][:10].capitalize(), #Fix distorted text
                    'partner'   : partner[:23],
            }
            ret.append(res_dict)
            tax_code_total += float(res[2])

        if not self.localcontext.get('tax_code_totals'):
            self.localcontext.update({'tax_code_totals' : {}})

        self.localcontext['tax_code_totals'].update({tax_id : tax_code_total})

        return ret


    def _get_tax_code_total(self, tax_id, context=None):
        totals = self.localcontext.get('tax_code_totals')
        total = 0.
        if totals:
            total = totals[tax_id]
        return '%0.2f' % total


    def _get_vat_box_str(self, tax_id, context=None):
        cr  = self.cr
        uid = self.uid
        tax_obj = self.pool.get('account.tax.code')
        tax = tax_obj.browse(cr, uid, tax_id, context=context)
        return 'VAT Box %s' % tax.code


    def _get_tax_code_name(self, tax_id, context=None):
        cr  = self.cr
        uid = self.uid
        tax_obj = self.pool.get('account.tax.code')
        return tax_obj.browse(cr, uid, tax_id, context=context).name


    def _get_date_limit(self, year, period, bound='low', context=None):
        cr  = self.cr
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


    def sort_result(self, accounts, context=None):
        # On boucle sur notre rapport
        result_accounts = []
        ind=0
        old_level=0
        while ind<len(accounts):
            #
            account_elem = accounts[ind]
            #

            #
            # we will now check if the level is lower than the previous level, in this case we will make a subtotal
            if (account_elem['level'] < old_level):
                bcl_current_level = old_level
                bcl_rup_ind = ind - 1

                while (bcl_current_level >= int(accounts[bcl_rup_ind]['level']) and bcl_rup_ind >= 0 ):
                    res_tot = { 'code': accounts[bcl_rup_ind]['code'],
                        'name': '',
                        'debit': 0,
                        'credit': 0,
                        'tax_amount': accounts[bcl_rup_ind]['tax_amount'],
                        'type': accounts[bcl_rup_ind]['type'],
                        'level': 0,
                        'pos': 0
                    }

                    if res_tot['type'] == 1:
                        # on change le type pour afficher le total
                        res_tot['type'] = 2
                        result_accounts.append(res_tot)
                    bcl_current_level =  accounts[bcl_rup_ind]['level']
                    bcl_rup_ind -= 1

            old_level = account_elem['level']
            result_accounts.append(account_elem)
            ind+=1

        return result_accounts



report_sxw.report_sxw('report.account.vat.invoices', 'account.tax.code',
    'addons/account_vat_report/report/account_tax_report.rml', parser=tax_report_invoices, header="internal")


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
 