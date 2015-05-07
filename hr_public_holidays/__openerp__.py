# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 credativ Ltd (<http://credativ.co.uk>).
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
    'name': 'Public Holidays',
    'version': '1.0',
    'category': 'Others',
    'description': """
Allows automatic calculation of public holidays based on rules.
This covers most holidays with the notable exception of Easter and
any one-off holidays which can be entered manually.

Not to be confused with and not related in any way with another module of the
same name which provides a far more simplistic management of public holidays.
    """,
    'author': 'credativ',
    'website': 'http://www.credativ.co.uk',
    'images': [],
    'depends': ['hr_holidays'],
    'init_xml': [],
    'update_xml': [
                   "security/ir.model.access.csv",
                   "public_holiday_view.xml", 
                   "holiday_data.xml",
                   ],
    'demo_xml': [],
    'test': [],
    'installable': True,
    'auto_install': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
