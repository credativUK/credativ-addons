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

{
    'name': "Bank account number validation",
    'summary': """Vaidates Normal Bank account number based on country""",

    'description': """
        It is crucial to perserve bank account number format for invoicing and
        other purposes. This module add a feature to validate bank account
        number based on country using python regular expression.
        Configuration:
            - To set bank account number regex go to Sales -> Configuration ->
              Address Book -> Localisation -> Countries
            - Open country and set regex in bank regex field e.g for uk bank
              account 00-00-00 12345678 use regex ^\d{2}-\d{2}-\d{2}\s\d{8}$
    """,

    'author': "credativ ltd",
    'website': "http://www.credativ.co.uk",
    'category': 'Accounting & Finance',
    'version': '0.1',
    'depends': ['base'],
    'data': [
        'views/res_country_view.xml',
    ],
    'active': False,
    'installable': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
