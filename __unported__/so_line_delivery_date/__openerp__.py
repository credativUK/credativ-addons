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
    'name' : 'Sale Order Line Delivery Dates',
    'version' : '1.0.0',
    'author' : 'credativ',
    'website' : 'http://credativ.co.uk',
    'depends' : [
        'sale',
        'sale_stock',
    ],
    'data' : [
        'security/sale_security.xml',
    ],
    'category' : 'Sales Management',
    'description': '''
Add functionality to set specific delivery dates on each sale order line.
''',
    'init_xml' : [
    ],
    'demo_xml' : [],
    'update_xml' : [
        'sale_view.xml',
        'res_config_view.xml',
    ],
    'installable': True
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
