# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2016 credativ Ltd (<http://credativ.co.uk>).
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
  'name': 'Phonecalls FreePBX UCP link',
  'version': '1.0',
  'category': 'Customer Relationship Management',
  'author': 'credativ ltd',
  'summary': """ Add link from phonecalls to the UCP in FreePBX """,
  'website': 'http://www.credativ.co.uk',
  'depends': ['crm_voip'],
  'data': [
      'views/crm_phonecall_view.xml',
  ],
  'license': 'AGPL-3',
}
