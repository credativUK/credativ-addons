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
    'name' : 'Procurement Sale Allocation',
    'version' : '1.0.0',
    'author' : 'credativ',
    'website' : 'http://credativ.co.uk',
    'depends' : [
        'procurement',
        'purchase',
        'sale',
        'sale_stock',
        'purchase_edit_utils',
    ],
    'category' : 'Sales & Purchases',
    'description': '''
This allows a procurement to change between the MTO and MTS workflows by being
allocated or deallocated to/from a purchase order. An automatic scheduler will
also allocate procurements to active purchase orders which have space available
for further allocations if the purchase order is flagged to allow allocations.
''',
    'init_xml' : [],
    'demo_xml' : [],
    'update_xml' : [
        "procurement_workflow.xml",
        "purchase_view.xml",
        "procurement_view.xml",
        "sale_view.xml",
        "stock_view.xml",
    ],
    'active': False,
    'installable': True
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
