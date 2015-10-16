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
    'name' : 'Product Cost Multi-Company',
    'version' : '1.0.0',
    'author' : 'credativ',
    'website' : 'http://credativ.co.uk',
    'depends' : [
        'product',
        'stock',
        'purchase',
        'account',
        'procurement',
        'product_variant_multi',
    ],
    'category' : 'Generic Modules/Product',
    'description': '''
Currently the cost price on a product is limited to a single currency and shared between all companies.
In a multi-company set up this means that it is impossible for each company to track a different cost price for each product.
This makes average pricing impossible.

This module adds functionality to read and write cost price based on the company of the related object, in the company currency.
Average pricing is the primary focus of this module, so modifications are made to stock moves so the related account moves are correct.
''',
    'init_xml' : [
        'security/product_security.xml',
        'security/ir.model.access.csv',
        ],
    'demo_xml' : [],
    'update_xml' : [
        "product_view.xml",
    ],
    'active': False,
    'installable': False
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
