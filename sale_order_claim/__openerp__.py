# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2013 credativ Ltd (<http://credativ.co.uk>).
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
    'name': 'Sale Order Claim',
    'version': '0.1',
    'category': 'Generic Modules/Sales & Purchases',
    'description': """This module customises crm.claim for sale orders.

The sale.order.claim model allows claims to be raised against a sale order, providing a variety of categories of claim. The sale.order.issue model allows problems to be registered against specific parts of a sale order which, again, can be of a variety of different categories. The issues are created as lines of the claim so that a single claim comprises multiple issues. Claims may also, however, have no issue lines and be just against the whole order (e.g. change of mind).

The module extends crm.claim providing a new crm.claim.line model (which is the super-model of sale.order.issue). It also provides a number of new states in which claims may be.

The module provides a crm.claim.resolution model which allows different kinds of resolutions to be defined and associated with claims. Resolutions may have a workflow.
""",
    'author': 'credativ Ltd',
    'website' : 'http://credativ.co.uk',
    'depends': ['sale','crm','crm_claim','account'],
    'init_xml': [],
    'update_xml': [
        'security/ir.model.access.csv',
        'sale_order_claim_sequence.xml',
        'crm_claim_view.xml',
        'sale_order_claim_view.xml',
        #'sale_order_issue_sale_order_line_view.xml',
        #'sale_order_issue_stock_move_view.xml'
        #'sale_order_issue_view.xml',
        #'wizard/create_order_issue.xml',
        #'sale_order_claim_view.xml',
        #'wizard/wizard_order_claim.xml',
    ],
    'demo_xml': [],
    'installable': True,
    'active': False,
    'certificate': '',
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
