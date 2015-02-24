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

{'name': 'Account Tax report detailed',
 'version': '1.0.0',
 'category': 'Account',
 'author': 'credativ Ltd',
 'website': 'http://www.credativ.co.uk',
 'license': 'AGPL-3',
 'description': """
New Tax report with invoice line
===============================

This module provides invoices details on VAT report

""",
 'depends': [
     'account',
 ],
 'data': [
     "wizard/account_vat_view.xml",
 ],
 'installable': True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: 
