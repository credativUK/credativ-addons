# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 credativ ltd (<http://www.credativ.co.uk>). All Rights Reserved
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
    'name': 'Credit Control Server Actions ',
    'version': '1.0',
    'category': 'Accounting & Finance',
    'description':
        """
        Add a server action channel to credit control.
        This module is an extention to account_credit_control module and
        allows server actions to be run instead of sending emails or letters
        which would allow more flexable functionality, such as scheduling
        follow up phonecalls.
        """,
    'author': 'credativ Ltd',
    'website' : 'http://credativ.co.uk',
    'depends': ['account_credit_control',],
    'init_xml': [],
    'update_xml': [
        'policy_view.xml',
        'credit_control_action_view.xml',
        'action_data.xml',
    ],
    'demo_xml': [],
    'installable': True,
    'active': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
