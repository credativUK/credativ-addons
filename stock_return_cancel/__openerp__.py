# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2016 credativ Ltd (<http://credativ.co.uk>).
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
    'name': 'Stock Return Cancel',
    'version': '1.0.0',
    'author': 'credativ',
    'website': 'http://credativ.co.uk',
    'depends': [
        'stock',
    ],
    'data': [],
    'category': 'Warehouse Management',
    'description': '''
Cancelling return products move lines will allow to re-return products from \
original picking.

Problem without this module:

* Create and confirm outgoing picking with a product of quantity 1

* Return the product by clicking return products button. This select the \
product and confirm.

* Cancel the newly incoming shipment created from returning products

* Go to original picking and try to return the same product(won't show in list)

''',
    'init_xml': [],
    'demo_xml': [],
    'update_xml': [],
    'installable': True
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
