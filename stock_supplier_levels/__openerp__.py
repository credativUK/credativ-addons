# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright 2015 credativ Ltd
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

{'name': 'Stock Supplier Levels',
 'version': '1.0.0',
 'category': 'stock',
 'author': 'credativ Ltd',
 'website': 'http://www.credativ.co.uk',
 'license': 'AGPL-3',
 'description': """
Stock Supplier Levels
=====================

This module allows creation of a new virtual location which
tracks what level of stock a supplier has available for
purchase. Purchase orders can also be set to order stock
from the supplier amount, which will deduct the supplier
stock level on confirmation.
""",
 'depends': [
     'product',
     'stock',
     'purchase',
 ],
 'data': [
     'stock_view.xml',
     'purchase_view.xml',
     'product_view.xml',
 ],
 'installable': True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
