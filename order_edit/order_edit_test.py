# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution    
#    Copyright (C) 2010 credativ Ltd (<http://credativ.co.uk>).
#    All Rights Reserved
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

# run with:
# bzr branch lp:millerpunittest # need to confirm this, should be 6.1 branch
# python ~/src/millerpunittest/run_unittests.py -- order_edit_test.SaleOrderTestCase


import datetime
import time
import netsvc

import millerpunittest.util as util

from osv import orm, osv


class SaleOrderTestCase(util.ERPTestCase):

    def setUp(self):
        super(SaleOrderTestCase, self).setUp()
        self.so_obj = self.pool.get('sale.order')
        self.product_id = util.duplicate_product(self, self.id_get('product.product_product_pc1'))

    def test_edit(self):
        order = util.create_empty_sale_order(self, {'order_policy': 'manual'})

        line = util.add_product_sale_order_line(self, order.id, self.id_get('product.product_product_worker0'), 1)
        self.assertEqual(line.product_id.type, 'service')
        order = self.click('sale.order', None, 'Confirm Order', order)

#        order = self.click('sale.order', None, 'Create Invoice', order)
        
#        so_invoice = self.click('account.invoice', None, 'Validate', order.invoice_ids[0])
#        so_debit = [payment for payment in so_invoice.move_id.line_id if payment.account_id == so_invoice.account_id][0]
#        payment_id = self.pool.get('sale.order').generate_payment_with_pay_code(self.cr, self.uid, 'paypal_standard', order.partner_id.id, so_debit.debit, order.name, order.name, order.date_order, True, {})
#        payment = self.pool.get('account.bank.statement.line').browse(self.cr, self.uid, payment_id)
#        so_credit_id = [pmnt.id for pmnt in payment.move_ids[0].line_id if pmnt.account_id.id == so_invoice.account_id.id][0]
#        rec_id = self.pool.get('account.move.line').reconcile(self.cr, self.uid, [so_debit.id, so_credit_id])
#        order = self.refresh(order)

#        po = util.create_made_purchase_order(self)
#        util.add_purchase_order_line(self, po.id, self.product_id, 2)
#        self.workflow(po, 'purchase_confirm')
#        po = self.workflow(po, 'purchase_approve')
#        batch_id = po.made_batches_batch_ids[0].id
#
#        for i in range(int(order.order_line[0].product_uom_qty)):
#            self.pool.get('made_batches.coi').create(self.cr, self.uid,
#                {'made_batch_id': batch_id,
#                 'product_id': order.order_line[0].product_id.id,
#                 'sale_order_id': order.id,
#                 'sale_order_line_id': order.order_line[0].id})
#        
#        self.workflow(order, 'manual_invoice') # create draft invoice
#        order = self.so_obj.browse(self.cr, self.uid, order.id)
#        self.workflow('account.invoice', order.invoice_ids[0].id, 'invoice_open') # confirm invoice

        edit_order_id = order.copy_for_edit()
        edit_order = self.so_obj.browse(self.cr, self.uid, edit_order_id)
        self.assertEqual(edit_order.origin, order.name)
        self.assertEqual(edit_order.name, order.name + '-edit1')

        line = util.add_product_sale_order_line(self, edit_order.id, self.id_get('product.product_product_employee0'), 1)
        self.assertEqual(line.product_id.type, 'service') 
        edit_order = self.click('sale.order', None, 'Confirm Order', edit_order)
        self.assertEqual(len(edit_order.order_line), 2)

        # old order cancelled
        order = self.refresh(order)
        self.assertEqual(order.state, 'cancel')
        invoice_ids = self.pool.get('account.invoice').search(self.cr, self.uid, [('name', '=', 'Edit Refund:%s' % order.name)])
        self.assertEqual(len(invoice_ids), 0) # no invoices yet
        #refund = self.pool.get('account.invoice').browse(self.cr, self.uid, invoice_ids[0])
        #self.assertEqual(refund.state, 'paid')

        # edit the edit
        edit2_order_id = edit_order.copy_for_edit()
        edit2_order = self.so_obj.browse(self.cr, self.uid, edit2_order_id)
        self.assertEqual(edit2_order.name, order.name + '-edit2')
        self.assertEqual(edit2_order.origin, edit_order.name)
        self.click('sale.order', None, 'Confirm Order', edit2_order)
        edit2_order = self.refresh(edit2_order)
        self.assertEqual(len(edit2_order.order_line), 2)

        edit_order = self.refresh(edit_order)
        
        self.assertEqual(self.pool.get('project.project').search(self.cr, self.uid, [('order_id', '=', order.id)]), [])
        edit_project = self.search_browse('project.project', [('order_id', '=', edit2_order.id)])
        self.assertEqual(set(task.name for task in edit_project.tasks), set(['Worker', 'Employee']))

