# -*- encoding: utf-8 -*-
##############################################################################
#
#    Account tax required module for OpenERP
#    Copyright (C) 2013 credativ ltd (http://www.credativ.co.uk). All Rights Reserved
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
    'name': 'Disable customer payments auto reconcile',
    'version': '0.1',
    'category': 'Generic Modules/Accounting',
    'license': 'AGPL-3',
    'description': """This module provides a feature to disable auto reconcile receipt vouchers.""",
    'author': 'credativ',
    'website': 'http://www.credativ.co.uk/',
    'depends': ['account_voucher'],
    'init_xml': [],
    'update_xml': [],
    'demo_xml': [],
    'installable': True,
    'active': False,
}

