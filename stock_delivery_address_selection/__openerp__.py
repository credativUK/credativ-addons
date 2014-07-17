# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2014 credativ Ltd (<http://credativ.co.uk>).
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
        'name' : 'Select Address on Delivery Orders',
        'version' : '0.1',
        'author' : 'credativ Ltd',
        'description' : """
This module allows users to specify a delivery address on Delivery Orders.
        """,
        'website' : 'http://credativ.co.uk',
        'depends' : [
            'stock',
            ],
        'init_xml' : [
            ],
        'update_xml' : [
            'stock_view.xml',
            ],
        'installable' : True,
        'active' : False,
}
