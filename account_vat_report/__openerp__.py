# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 credativ Ltd (<http://credativ.co.uk>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
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
