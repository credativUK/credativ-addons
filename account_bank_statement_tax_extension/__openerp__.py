# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 credativ ltd (<http://credativ.co.uk>).
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
    'name': 'Apply a tax on bank statement lines extension',
    'version': '0.1',
    'license': 'AGPL-3',
    'author': "credativ uk ltd",
    'website': 'http://credativ.co.uk',
    'category': 'Banking addons',
    'depends': [
        'account_bank_statement_tax',
        'web_m2x_options',
    ],
    'data': [
        'view/account_bank_statement.xml',
    ],
    'description': '''
This module converts TAX on statement line to selection only field
    ''',
    'installable': True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
