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
    'name': 'Timesheet Line Replication',
    'version': '1.0',
    'category': 'Human Resources',
    'description': """
    Timesheet lines are given a button which allow the user to replicate the line for an arbitrary number of dates.
    """,
    'author': 'credativ ltd',
    'website': 'http://www.credativ.co.uk',
    'images': [],
    'depends': ['hr_timesheet',
    ],
    'init_xml': [],
    'update_xml': [
      'hr_timesheet_line_replicate_view.xml',
      'wizard/hr_timesheet_line_replicate_wizard_view.xml',
    ],
    'demo_xml': [],
    'test': [],
    'installable': True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
