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
    'name': 'Sale Damage Log',
    'version': '1.0',
    'category': 'Generic Modules/Sales & Purchases',
    'description': """This Module allows you to manage the log for damaged products.""",
    'author': 'credativ Ltd',
    'website' : 'http://credativ.co.uk',
    'depends': ['sale','crm','account'],
    'init_xml': [],
    'update_xml': [
        'security/ir.model.access.csv',
        'sale_damagelog_view.xml',
        'sale_comprequest_view.xml',
        'sale_comprequest_sequence.xml',
    ],
    'demo_xml': [],
    'installable': True,
    'active': False,
    'certificate': '',
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
