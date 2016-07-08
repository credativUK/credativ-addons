# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright 2016 credativ Ltd
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
    'name' : 'Web Export Permissions',
    'version' : '1.0',
    'depends' : ['base',
                 'web_action_permissions',
                ],
    'author': 'credativ Ltd',
    'website': 'http://www.credativ.co.uk',
    'license': 'AGPL-3',
    'category': 'Web',
    'description': """
The 'Export' button will be available only to users with suitable permissions.
    """,
    'data': [],
    'update_xml': [
        'ir_rule_view.xml',
    ],
    'installable': True,
    'auto_install': True,
    'web': True,
    'js': ['static/src/js/view_list.js'],
    'css': [],
    'qweb' : [],
    'post_load': 'post_load',
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
