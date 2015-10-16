# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2014 credativ ltd (<http://www.credativ.co.uk>). All Rights Reserved
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
    'name': 'Service on Picking and Invoice',
    'version': '0.0.1',
    'author': 'credativ Ltd',
    'website' : 'http://credativ.co.uk',
    'category' : 'Inventory, Logistic, Storage',
    'depends': ['sale', 'stock', 'sale_stock'],
    'description': """
Service on Picking and Invoice
==============================

This module is designed to provide a quick and simple way to show services on pickings (for example for delivery services)
and also have them added to the invoice from a picking for billing.

Warning: This module is a quick workaround and not designed as a complete solution.
Please note the following limitations:
* All services are only shown on the picking form view from the related sale order
* Services are not included in the picking report generated from the picking object
* All services are entered into the invoice when created from the picking
* If split pickings are used, all services are shown on all pickings
* Invoicing from split pickings will result in services being entered multiple times - they must be corrected manually
    """,
    'data': [
        'stock_view.xml',
    ],
    'auto_install': False,
    'installable': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
