# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution	
#    Copyright (C) 2012 credativ ltd (<http://www.credativ.co.uk>). All Rights Reserved
#    $Id$
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
    'name': 'stock_levels',
    'version': '0.6',
    'category': 'Generic Modules/Inventory Control',
    'description': """
    Adds a new view showing current stock levels for each product and location.

    This module is similar to the stock by location view, but it does not show
    empty locations or their parent locations, and allows filtering by product and location.
    """,
    'author': 'credativ',
    'depends': ['stock'],
    #'update_xml': ['stock_levels_view.xml',
    #                'security/ir.model.access.csv'],
    'update_xml': ['stock_levels_view.xml'],
    'demo_xml': [],
    'installable': True,
    'active': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
