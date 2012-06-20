## -*- encoding: utf-8 -*-
###############################################################################
##
##    OpenERP, Open Source Management Solution
##    Copyright (C) 2011 credativ ltd (<http://www.credativ.co.uk>). All Rights Reserved
##
##    This program is free software: you can redistribute it and/or modify
##    it under the terms of the GNU General Public License as published by
##    the Free Software Foundation, either version 3 of the License, or
##    (at your option) any later version.
##
##    This program is distributed in the hope that it will be useful,
##    but WITHOUT ANY WARRANTY; without even the implied warranty of
##    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
##    GNU General Public License for more details.
##
##    You should have received a copy of the GNU General Public License
##    along with this program.  If not, see <http://www.gnu.org/licenses/>.
##
###############################################################################

from osv import fields, osv

class sale_order(osv.osv):
    
    _inherit = "sale.order"

    _columns = {
        'order_policy': fields.selection([
            ('prepaid', 'Payment Before Delivery'),
            ('manual', 'Shipping & Manual Invoice'),
            ('postpaid', 'Invoice On Order After Delivery'),
            ('picking', 'Invoice From The Picking'),
            ('automatic', 'Automatic After Delivery'),
            ], 'Shipping Policy', required=True, readonly=True, states={'draft': [('readonly', False)]},
            help="""The Shipping Policy is used to synchronise invoice and delivery operations.
            - The 'Pay Before delivery' choice will first generate the invoice and then generate the picking order after the payment of this invoice.
            - The 'Shipping & Manual Invoice' will create the picking order directly and wait for the user to manually click on the 'Invoice' button to generate the draft invoice.
            - The 'Invoice On Order After Delivery' choice will generate the draft invoice based on sales order after all picking lists have been finished.
            - The 'Invoice From The Picking' choice is used to create an invoice during the picking process.
            - The 'Automatic After Delivery' will automatically generate the invoice after delivery of order based on shipped amount"""),
    }
    
    def shipping_policy_change(self, cr, uid, ids, policy, context=None):
        res = super(sale_order, self).shipping_policy_change(cr, uid, ids, policy, context=context)
        if policy == 'automatic':
            res = 'procurement'
        return {'value': {'invoice_quantity': res}}
   
sale_order()
            