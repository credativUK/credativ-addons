# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2017 credativ Ltd (<http://credativ.co.uk>).
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
    'name': 'Export Product Images',
    'version': '1.0',
    'category': 'Sales Management',
    'sequence': 20,
    'summary': 'To Export selected product images to a specified directory',
    'description': """
Export selected product images to a specified directory
==================================

This application allows you to Export selected product images to a specified directory.
    """,
    'author': 'credativ software (India) pvt ltd',
    'depends': ['product'],
    'data': [
        'wizard/export_product_images_view.xml',
    ],
    'demo': [],
    'test': [
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
