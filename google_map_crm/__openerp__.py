# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 credativ Ltd (<http://credativ.co.uk>).
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
    'name': 'Google Maps on CRM',
    'version': '1.0',
    'category': 'Customer Relationship Management',
    'description': """
The module adds Google Map field in leads and meetings.
====================================================

Using this you can directly open Google Map from the URL widget.""",
    'author': 'credativ Ltd',
    'website': 'http://www.credativ.co.uk',
    'depends': ['crm', 'google_map'],
    'init_xml': [],
    'update_xml': [
                   'google_map_view.xml',
                  ],
    'demo_xml': [],
    'installable': True,
    'auto_install': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
