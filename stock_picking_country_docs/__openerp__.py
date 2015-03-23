# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution   
#    Copyright (C) 2015 credativ ltd (<http://www.credativ.co.uk>). All Rights Reserved
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
    'name': 'Country shipping documents',
    'version':'1.0',
    'category' : 'Warehouse',
    'description': """
This module provides functionality to copy shipping documentation on to pickings.

* Shipping documentation can be attached to country records
* Clicking the "Attach shipping documentation" button on the picking will copy all attachments from the destination country record
    """,
    'author' : 'credativ',
    'website' : 'http://www.credativ.co.uk',
    'depends':[
               'stock',
               ],
    'update_xml' : [
        'stock_picking_view.xml'
    ],
    'auto_install': False,
    'installable': True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
