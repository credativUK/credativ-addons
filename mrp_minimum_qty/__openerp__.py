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
  'name': 'Minimum manufacturing quantity',
  'version': '1.0',
  'category': 'Manufacturing',
  'complexity': 'medium',
  'description': "This module lets the user define a minimum quantity on a BoM and does not create a manufacturing order until enough procurements are raised to create a single manufacturing order.",
  'author': 'credativ ltd',
  'website': 'http://www.credativ.co.uk',
  'depends': ['mrp'],
  'data' : ['mrp_bom_view.xml'],
  'installable': True,
}
