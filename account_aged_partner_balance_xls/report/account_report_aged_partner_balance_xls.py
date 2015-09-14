# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 credativ Ltd (<http://credativ.co.uk>).
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

import xlwt
import time
from datetime import datetime
from openerp.osv import orm
from openerp.report import report_sxw
from openerp.addons.report_xls.report_xls import report_xls
from openerp.addons.report_xls.utils import rowcol_to_cell, _render
from openerp.addons.account.report.account_aged_partner_balance import aged_trial_report
from openerp.tools.translate import _
import logging
_logger = logging.getLogger(__name__)


class account_report_aged_partner_balance_xls_parser(aged_trial_report):

    def __init__(self, cr, uid, name, context):
        super(account_report_aged_partner_balance_xls_parser, self).__init__(cr, uid, name, context=context)
        self.context = context
        self.localcontext.update({
            '_': _,
            'time': time,
            'get_lines_with_out_partner': self._get_lines_with_out_partner,
            'get_lines': self._get_lines,
            'get_total': self._get_total,
            'get_direction': self._get_direction,
            'get_for_period': self._get_for_period,
            'get_company': self._get_company,
            'get_currency': self._get_currency,
            'get_partners':self._get_partners,
            'get_account': self._get_account,
            'get_fiscalyear': self._get_fiscalyear,
            'get_target_move': self._get_target_move,
        })

class account_report_aged_partner_balance_xls(report_xls):

    def __init__(self, name, table, rml=False, parser=False, header=True, store=False):
        super(account_report_aged_partner_balance_xls, self).__init__(name, table, rml, parser, header, store)

        # Cell Styles
        _xs = self.xls_styles
        # header
        rh_cell_format = _xs['bold'] + _xs['fill'] + _xs['borders_all']
        self.rh_cell_style = xlwt.easyxf(rh_cell_format)
        self.rh_cell_style_center = xlwt.easyxf(rh_cell_format + _xs['center'])
        self.rh_cell_style_right = xlwt.easyxf(rh_cell_format + _xs['right'])
        # lines
        aml_cell_format = _xs['borders_all']
        self.aml_cell_style = xlwt.easyxf(aml_cell_format)
        self.aml_cell_style_center = xlwt.easyxf(aml_cell_format + _xs['center'])
        self.aml_cell_style_date = xlwt.easyxf(aml_cell_format + _xs['left'], num_format_str=report_xls.date_format)
        self.aml_cell_style_decimal = xlwt.easyxf(aml_cell_format + _xs['right'], num_format_str=report_xls.decimal_format)
        # totals
        rt_cell_format = _xs['bold'] + _xs['fill'] + _xs['borders_all']
        self.rt_cell_style = xlwt.easyxf(rt_cell_format)
        self.rt_cell_style_right = xlwt.easyxf(rt_cell_format + _xs['right'])
        self.rt_cell_style_decimal = xlwt.easyxf(rt_cell_format + _xs['right'], num_format_str=report_xls.decimal_format)

        self.col_specs_header_template = {
            'chart_name': {
                'header': [2, 40, 'text', _render("_('Chart of Accounts')")],
                'lines': [2, 40, 'text', _render("get_account(data)")],},
            'fiscal_year': {
                'header': [2, 40, 'text', _render("_('Fiscal Year')")],
                'lines': [2, 40, 'text', _render("get_fiscalyear(data)"), None, self.aml_cell_style_date],},
            'date_start': {
                'header': [2, 40, 'text',  _render("_('Start Date')")],
                'lines': [2, 40, 'text', _render("formatLang(data['form']['date_from'], date=True)")],},
            'period_length': {
                'header': [2, 40, 'text', _render("_('Period Length')")],
                'lines': [2, 40, 'number', _render("data['form']['period_length']")],},
            'account_type': {
                'header': [2, 40, 'text', _render('_("Partner\'s")')],
                'lines': [2, 40, 'text', _render("data['form']['result_selection'] == 'customer' and 'Receivable Accounts'" \
                    " or data['form']['result_selection'] == 'supplier' and 'Payable Accounts'" \
                    " or data['form']['result_selection'] == 'customer_supplier' and 'Receivable and Payable Accounts'")],},
            'direction': {
                'header': [2, 40, 'text', _render("_('Analysis Direction')")],
                'lines': [2, 40, 'text', _render("data['form']['direction_selection']")],},
            'moves': {
                'header': [2, 40, 'text', _render("_('Target Moves')")],
                'lines': [2, 40, 'text', _render("get_target_move(data)")],},
        }

        self.col_specs_data_template_wanted = ['partner', 'due', 'period4', 'period3', 'period2', 'period1', 'period0', 'total']
        self.col_specs_data_template = {
            'partner': {
                'header': [1, 40, 'text', _render("_('Partners')")],
                'total': [1, 40, 'text', _render("_('Account Total')")],
                'line': [1, 40, 'text', _render("partner['name']")],
                'line_not_partner': [1, 40, 'text', _render("not_partner['name']")],},
            'due': {
                'header': [1, 20, 'text', _render("data['form']['direction_selection'] == 'future' and _('Due') or _('Not Due')")],
                'total': [1, 20, 'number', _render("formatLang(get_direction(6))")],
                'line': [1, 20, 'number', _render("formatLang(partner['direction'])")],
                'line_not_partner': [1, 40, 'number', _render("formatLang(not_partner['direction'])")],},
            'period4': {
                'header': [1, 20, 'text', _render("data['form']['4']['name']")],
                'total': [1, 20, 'number', _render("formatLang(get_for_period(4))")],
                'line': [1, 20, 'number', _render("formatLang(partner['4'])")],
                'line_not_partner': [1, 40, 'number', _render("formatLang(not_partner['4'])")],},
            'period3': {
                'header': [1, 20, 'text', _render("data['form']['3']['name']")],
                'total': [1, 20, 'number', _render("formatLang(get_for_period(3))")],
                'line': [1, 20, 'number', _render("formatLang(partner['3'])")],
                'line_not_partner': [1, 40, 'number', _render("formatLang(not_partner['3'])")],},
            'period2': {
                'header': [1, 20, 'text', _render("data['form']['2']['name']")],
                'total': [1, 20, 'number', _render("formatLang(get_for_period(2))")],
                'line': [1, 20, 'number', _render("formatLang(partner['2'])")],
                'line_not_partner': [1, 40, 'number', _render("formatLang(not_partner['2'])")],},
            'period1': {
                'header': [1, 20, 'text', _render("data['form']['1']['name']")],
                'total': [1, 20, 'number', _render("formatLang(get_for_period(1))")],
                'line': [1, 20, 'number', _render("formatLang(partner['1'])")],
                'line_not_partner': [1, 40, 'number', _render("formatLang(not_partner['1'])")],},
            'period0': {
                'header': [1, 20, 'text', _render("data['form']['0']['name']")],
                'total': [1, 20, 'number', _render("formatLang(get_for_period(0))")],
                'line': [1, 20, 'number', _render("formatLang(partner['0'])")],
                'line_not_partner': [1, 40, 'number', _render("formatLang(not_partner['0'])")],},
            'total': {
                'header': [1, 20, 'text', _render("_('Total')")],
                'total': [1, 20, 'number', _render("formatLang(get_for_period(5))")],
                'line': [1, 20, 'number', _render("formatLang(partner['total'])")],
                'line_not_partner': [1, 40, 'number', _render("formatLang(not_partner['total'])")],},
        }

    def _report_title(self, data, ws, _p, row_pos, xlwt, _xs):
        cell_style = xlwt.easyxf(_xs['xls_title'])

        # Main Title
        c_specs = [
            ('report_name', 8, 0, 'text', _("Aged Trial Balance")),
        ]
        row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
        row_pos = self.xls_write_row(ws, row_pos, row_data, row_style=cell_style)
        row_pos += 1

        # Rows of Parameters
        wanted_lists = [['chart_name', 'fiscal_year', 'date_start', 'period_length'], ['account_type', 'direction', 'moves']]
        for wanted_list in wanted_lists:
            c_specs = map(lambda x: self.render(x, self.col_specs_header_template, 'header', render_space={'_': _p._}), wanted_list)
            row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
            row_pos = self.xls_write_row(ws, row_pos, row_data, row_style=self.rh_cell_style)
            c_specs = map(lambda x: self.render(x, self.col_specs_header_template, 'lines'), wanted_list)
            row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
            row_pos = self.xls_write_row(ws, row_pos, row_data, row_style=self.rh_cell_style)
            row_pos += 1

        # Headers
        c_specs = map(lambda x: self.render(x, self.col_specs_data_template, 'header',), self.col_specs_data_template_wanted)
        row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
        row_pos = self.xls_write_row(ws, row_pos, row_data, row_style=self.rh_cell_style)
        return row_pos

    def _report_totals(self, data, ws, _p, row_pos, xlwt, _xs):
        cell_style = xlwt.easyxf(_xs['xls_title'])

        # Headers

        if _p.get_lines(_p.data['form']) or _p.get_lines_with_out_partner(_p.data['form']): # FIXME: Should we use render here?
            c_specs = map(lambda x: self.render(x, self.col_specs_data_template, 'total'), self.col_specs_data_template_wanted)
            row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
            row_pos = self.xls_write_row(ws, row_pos, row_data, row_style=self.rt_cell_style_decimal, set_column_size=True)
        return row_pos

    def _report_lines(self, data, ws, _p, row_pos, xlwt, _xs):
        cell_style = xlwt.easyxf(_xs['xls_title'])

        # Partners
        for partner in _p.get_lines(_p.data['form']): # FIXME: Should we use render here?
            _p.partner = partner # FIXME: Surely there is a nicer way of doing this
            c_specs = map(lambda x: self.render(x, self.col_specs_data_template, 'line',), self.col_specs_data_template_wanted)
            row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
            row_pos = self.xls_write_row(ws, row_pos, row_data, row_style=self.aml_cell_style)

        # Non Partners
        for not_partner in _p.get_lines_with_out_partner(_p.data['form']): # FIXME: Should we use render here?
            _p.not_partner = not_partner # FIXME: Surely there is a nicer way of doing this
            c_specs = map(lambda x: self.render(x, self.col_specs_data_template, 'line_not_partner',), self.col_specs_data_template_wanted)
            row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
            row_pos = self.xls_write_row(ws, row_pos, row_data, row_style=self.aml_cell_style)

        return row_pos

    def generate_xls_report(self, _p, _xs, data, objects, wb):
        sheet_name = 'Aged Partner Balance'
        ws = wb.add_sheet(sheet_name)
        ws.panes_frozen = True
        ws.remove_splits = True
        ws.portrait = 0  # Landscape
        ws.fit_width_to_pages = 1
        row_pos = 0

        # set print header/footer
        ws.header_str = self.xls_headers['standard']
        ws.footer_str = self.xls_footers['standard']

        # Data
        row_pos = self._report_title(data, ws, _p, row_pos, xlwt, _xs)
        row_pos = self._report_totals(data, ws, _p, row_pos, xlwt, _xs)
        row_pos = self._report_lines(data, ws, _p, row_pos, xlwt, _xs)

account_report_aged_partner_balance_xls('report.account_aged_partner_balance_xls.report_agedpartnerbalance_xls', 'account.account',
    parser=account_report_aged_partner_balance_xls_parser)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
