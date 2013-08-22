# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2013 credativ Ltd (<http://credativ.co.uk>).
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
    "name" : "Sale Report Supplier",
    "version" : "1.0",
    "author" : "credativ Ltd",
    "category": 'Sale',
    'complexity': "easy",
    "description": """
Report to list sales of products grouped by their default supplier.
Products defined by a BoM will list all componant products that create the BoM
    """,
    'website': 'http://www.credativ.co.uk',
    'init_xml': [],
    "depends" : ["sale", "mrp"],
    'update_xml': [
        'sale_report_supplier.xml',
    ],
    'demo_xml': [
    ],
    'installable': True,
    'auto_install': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
