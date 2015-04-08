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
    'name': 'Purchase Order Edit',
    'version': '1.0',
    'category': 'Sales & Purchases',
    'description':
        """
        Purchase Order Edit
        """,
    'author': 'credativ Ltd',
    'website' : 'http://credativ.co.uk',
    'depends': [
        'base_order_edit',
        'purchase_edit_utils',
        'procurement',
        'purchase',
        'mail',
        ],
    'init_xml': [
        ],
    'update_xml': [
        'wizard/purchase_order_edit_wizard_view.xml',
        'purchase_view.xml'
    ],
    'demo_xml': [
    ],
    'installable': True,
    'active': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
