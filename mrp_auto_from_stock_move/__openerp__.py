# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2012 credativ Ltd (<http://credativ.co.uk>).
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
    "name" : "Delivery Driven Automatic Manufacturing",
    "version" : "1.1",
    "author" : "credativ Ltd",
    'website' : 'http://credativ.co.uk',
    "category" : "Manufacturing",
    "sequence": 18,
    "images" : [],
    "depends" : [
        "mrp",
        ],
    "description": """
This is the base module to manage the manufacturing process in OpenERP.
=======================================================================

Features:
---------
    As soon as an outgoing raw materials shipment to the subcontractor is completed, 
    the corresponding incoming shipment of the Finished Products will be visible and 
    available in the Incoming Shipments screen.
    """,
    'init_xml': [],
    'update_xml': [
        'mrp_workflow.xml',
        'mrp_view.xml',
    ],
    'demo_xml': [],
    'test': [],
    'installable': True,
    'active': False,
    'certificate': '',
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
