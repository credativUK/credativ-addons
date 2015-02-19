# -*- coding: utf-8 -*-
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
  'name': 'Sales Order Dimensions',
  'version': '1.0',
  'category': 'Sale',
  'complexity': 'easy',
  'description': "This module adds a Weight and Volume fields on the Sale Order to gauge the size of the order, also adds the volume field on the picking.",
  'author': 'credativ UK',
  'website': 'http://www.credativ.co.uk',
  'depends': ['sale', 'delivery'],
  'init_xml': [],
  'update_xml' : [
      'sale_order_view.xml',
      'stock_picking_view.xml',
      ],
  'demo_xml': [],
  'installable': True,
}
