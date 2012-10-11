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
    'name' : 'Partner Fraud Flag',
    'version' : '1.0.0.0',
    'author' : 'credativ Ltd',
    'website' : 'http://credativ.co.uk',
    'depends' : [
        'base',
        'sale',
    ],
    'category' : 'Custom Modules',
    'description': '''
A manual flag for Fraud set on Partners which will show in Sale Orders
''',
    'init_xml' : [
    ],
    'demo_xml' : [
    ],
    'update_xml' : [
        'res_partner_view.xml',
        'sale_view.xml',
    ],
    'active': False,
    'installable': True
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
