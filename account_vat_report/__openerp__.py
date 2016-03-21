# -*- coding: utf-8 -*-
#    Copyright (C) 2016 credativ Ltd (<http://credativ.co.uk>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    'name': 'Account Tax Teport Detailed',
    'application': False,
    'version': '8.0.1.0',
    'category': 'Account',
    'author': 'credativ Ltd',
    'website': 'http://www.credativ.co.uk',
    'license': 'AGPL-3',
    "depends": [
        'account'
    ],
    'installable': True,
    'data': [
        'views/account_vat_view.xml',
        'views/report_vat.xml',
    ],
}
