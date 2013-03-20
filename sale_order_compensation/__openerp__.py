# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2013 credativ Ltd (<http://credativ.co.uk>).
#    All Rights Reserved
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
{
    'name': 'Sale Order Compensation',
    'version': '0.1',
    'category': 'Generic Modules/Sales & Purchases',
    'description': """This module customises sale order claims for compensation resolutions.

It adds new fields to sale.order.claim and sale.order.issue for retrieving information on refunds and vouchers issued against sale orders.
""",
    'author': 'credativ Ltd',
    'website' : 'http://credativ.co.uk',
    'depends': ['sale_order_claim'],
    'init_xml': [],
    'update_xml': [
        #'sale_order_compensation_data.xml',
        'sale_order_compensation_view.xml',
        #'wizard/create_order_claim.xml',
    ],
    'demo_xml': [],
    'installable': True,
    'active': False,
    'certificate': '',
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
