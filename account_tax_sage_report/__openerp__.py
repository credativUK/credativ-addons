# -*- coding: utf-8 -*-
# © 2016 Kinner Vachhani <kinner.vachhani@credativ.co.uk>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Account Sage Tax Report',
    'version': '1.0.0',
    'category': 'Accounting & Finance',
    'summary': 'Sage like Tax Report',
    'license': 'AGPL-3',
    'depends': [
        'account',
    ],
    'author': 'credativ Ltd',
    'website': 'http://www.credativ.co.uk',
    'data': [
        'wizard/account_vat_view.xml',
        'view/account_report.xml',
        'view/report_vat.xml',
    ],
    'installable': True,
}
