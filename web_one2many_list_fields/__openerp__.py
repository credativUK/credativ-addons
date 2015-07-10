# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright 2015 credativ Ltd
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
    'name' : 'Web One2Many with Fields',
    'version' : '1.0',
    'depends' : ['base'],
    'author': 'credativ Ltd',
    'website': 'http://www.credativ.co.uk',
    'license': 'AGPL-3',
    'category': 'Tools',
    'description': """
Allows additional fields to be displayed below a one2many list view in the last row during editing
    """,
    'data': [],
    'installable': True,
    'auto_install': True,
    'web': True,
    'js': ['static/src/js/view.js'],
    'css': [],
    'qweb' : [],
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
