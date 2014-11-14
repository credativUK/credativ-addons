# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2014 credativ Ltd (<http://credativ.co.uk>).
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
    'name': 'Zero Value Sale Order Workflow',
    'description':
        '''
        The basic Sale Order automatic invoice workflow requires that an
        invoice be created and paid before the order progresses to 'done'.
        This module prevents this from happening if the Sale Order has
        zero value.
        ''',
    'version': '1.0',
    'author': 'credativ Ltd',
    'website': 'http://credativ.co.uk',
    'category': '',
    'depends': [
        'sale_stock',
        ],
    'data': [
        'sale_workflow.xml',
        ],
    'installable': True,
    'active': False,
}
