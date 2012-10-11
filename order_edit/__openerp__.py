# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution    
#    Copyright (C) 2012 credativ Ltd (<http://credativ.co.uk>).
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
    'name': 'Sale Order Edit',
    'version': '0.1',
    'category': 'Sales & Purchases',
    'description':
        """
        Sale Order Edit
        """,
    'author': 'credativ Ltd',
    'website' : 'http://credativ.co.uk',
    'depends': [
        'sale',
        'purchase',
        'mail',
        'base_sale_multichannels' # for sale_order.generate_payment_with_pay_code
        ],
    'init_xml': [
        ],
    'update_xml': [
        'wizard/order_edit_wizard_view.xml',
    ],
    'demo_xml': [
    ],
    'installable': True,
    'active': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
