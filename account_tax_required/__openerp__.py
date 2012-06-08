# -*- encoding: utf-8 -*-
##############################################################################
#
#    Account tax required module for OpenERP
#    Copyright (C) 2011 Akretion (http://www.akretion.com). All Rights Reserved
#    Copyright (C) 2011 credativ ltd (http://www.credativ.co.uk). All Rights Reserved
#    @author Alexis de Lattre <alexis.delattre@akretion.com>
#    @author Dmitrijs Ledkovs <dmitrijs.ledkovs@credativ.co.uk>
#    Fork off account analytic required module, to make taxes mandatory
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
    'name': 'Account tax required',
    'version': '0.1',
    'category': 'Generic Modules/Accounting',
    'license': 'AGPL-3',
    'description': """This module adds an option "tax policy" on account types. You have the choice between 3 policies : always, never and optional.

For example, if you want to have an tax account on all your expenses, set the policy to "always" for the account type "expense" ; then, if you try to save an account move line with an account of type "expense" without tax account, you will get an error message.

This module is based on the account analytic required module by Akretion.
""",
    'author': 'credativ',
    'website': 'http://www.credativ.co.uk/',
    'depends': ['account'],
    'init_xml': [],
    'update_xml': ['account_view.xml'],
    'demo_xml': [],
    'installable': True,
    'active': False,
}

