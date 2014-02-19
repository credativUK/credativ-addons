# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution	
#    Copyright (C) 2013 credativ ltd (<http://www.credativ.co.uk>). All Rights Reserved
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
    'name': 'Deferred Actions',
    'version': '0.2',
    'category': 'Generic Modules/Base',
    'description': """This module provides the abillity to defer user actions to a queue.""",
    'author': 'credativ',
    'depends': [
        'base',
    ],
    'update_xml': [
        'deferred_action_data.xml',
        'deferred_action_view.xml',
        'wizard/deferred_action_notification_view.xml',
        'security/ir.model.access.csv',
    ],
    'demo_xml': [],
    'installable': True,
    'active': False,
}