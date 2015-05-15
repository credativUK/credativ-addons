# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2014 credativ Ltd (<http://credativ.co.uk>).
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
        'name' : 'Specify Stock Return Locations',
        'version' : '0.1',
        'author' : 'credativ Ltd',
        'description' : """
When processing a stock return, this module allows the user to specify a
custom location to which the returned stock will be sent.
        """,
        'website' : 'http://credativ.co.uk',
        'depends' : [
            'stock',
            ],
        'init_xml' : [
            ],
        'update_xml' : [
            'wizard/stock_return_picking_view.xml',
            ],
        'installable' : True,
        'active' : False,
}
