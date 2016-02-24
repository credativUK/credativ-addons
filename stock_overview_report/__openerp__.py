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
    'name' : 'Stock Overview Report',
    'version' : '1.0.0',
    'author' : 'credativ',
    'website' : 'http://credativ.co.uk',
    'depends' : [
        'stock',
    ],
    'category' : 'Warehouse Management',
    'description': '''
Adds a wizard which takes a stock level snapshot from all warehouses at a time specified.
The report displays stock level of products per company and warehouse and allows grouping.
Due the snapshot of the data, changing filters is quick since data does not need to be
recalculated, which is slow for stock level calculations.
''',
    'init_xml' : [],
    'demo_xml' : [],
    'update_xml' : [
        'stock_overview_report_view.xml',
        'stock_overview_report_data.xml',
        'security/ir.model.access.csv',
    ],
    'active': True,
    'installable': True,
    'auto_install': False,
    'application': True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
