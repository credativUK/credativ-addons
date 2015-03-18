# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2013-2015 credativ Ltd (<http://credativ.co.uk>).
#    All Rights Reserved
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
  'name': 'HR Holidays \'Covering Person\' field for leave requests.',
  'version': '1.0',
  'category': 'HR',
  'complexity': 'easy',
  'description': "This module adds a form element to the HR Holidays module for the name of the person to cover an employee's work when they create a leave request.",
  'author': 'credativ ltd',
  'website': 'http://www.credativ.co.uk',
  'depends': ['hr_holidays'],
  'data' : ['hr_holidays_covering_view.xml'],
  'installable': True,
}
