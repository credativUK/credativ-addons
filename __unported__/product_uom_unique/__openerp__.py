# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2014 credativ Ltd (<http://credativ.co.uk>).
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
    'name' : 'Purchase Orders by Unit Quantity',
    'version' : '1.0.0',
    'author' : 'credativ',
    'website' : 'http://credativ.co.uk',
    'depends' : [
        'base',
        'purchase',
        'sale',
    ],
    'category' : 'Generic Modules/Purchase',
    'description': '''
This module will add functionality to choose quantity on purchase order lines by unit quantity or quantity of units of measure (UoMs).
Modifying one will calculate the other automatically depending on the UoM.
Products can also be assigned to specific UoMs.  This results in that particular UoM only appearing on the associated products.
If no products are allocated to a UoM, this UoM is available to all products.

''',
    'init_xml' : [],
    'demo_xml' : [],
    'update_xml' : [
        "purchase_view.xml",
        "product_view.xml",
        "sale_view.xml",
    ],
    'active': False,
    'installable': True
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
