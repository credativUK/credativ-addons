# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2012 credativ ltd (http://www.credativ.co.uk). All Rights Reserved
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
    'name': 'Bank Statements View Currency Modification',
    'version': '0.1',
    'category': 'Generic Modules/Accounting',
    'license': 'AGPL-3',
    'description': """This module adds currency columns to the bank statement screens.""",
    'author': 'credativ Ltd',
    'website': 'http://www.credativ.co.uk/',
    'depends': ['account'],
    'init_xml': [],
    'update_xml': ['account_view.xml'],
    'demo_xml': [],
    'installable': True,
    'active': False,
}

