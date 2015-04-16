import time
from openerp.tests.common import TransactionCase

class TestCredit(TransactionCase):
    def setUp(self):
        super(TestCredit, self).setUp()
        self.InvoiceObj = self.env['account.invoice']
        self.InvoiceWizard = self.env['sale.advance.payment.inv']
        self.OrderObj = self.env['sale.order']
        self.VoucherObj = self.env['account.voucher']

        self.partner_company = self.env.ref('base.res_partner_15')
        self.partner_contact = self.env.ref('base.res_partner_address_25')

        self.product_service = self.env.ref('product.product_product_consultant')
        self.bank_journal = self.env.ref('account.bank_journal')

        self.order = self.OrderObj.create({
            'partner_id': self.partner_contact.id,
            'order_policy': 'manual',
            'order_line': [(0, 0, {
                'product_id': self.product_service.id,
                'product_uom': self.product_service.uom_id.id,
                'product_uom_qty': 1,
                'price_unit': 100,
            })],
        })

    def test_00_credit(self):
        self.assertEqual(self.partner_company.credit, 2240.0, "Credit information inaccurate")

        # confirm self.order
        self.order.signal_workflow('order_confirm')
        self.assertEqual(self.partner_company.credit, 2340.0, "Credit information inaccurate")
        self.assertEqual(len(self.order.invoice_ids), 0, "Unexpected invoice on order")

        # partially invoice self.order
        wizard = self.InvoiceWizard.with_context({
            'active_id': self.order.id,
            'active_ids': [self.order.id],
        }).create({
            'advance_payment_method': 'fixed',
            'amount': 40,
        })
        wizard.create_invoices()

        self.assertEqual(len(self.order.invoice_ids), 1, "Unexpected invoice on order")
        invoice = self.order.invoice_ids[0]

        self.assertEqual(self.partner_company.credit, 2340.0, "Credit information inaccurate")
        invoice.signal_workflow('invoice_open')

        self.assertEqual(self.partner_company.credit, 2340.0, "Credit information inaccurate")

        # pay invoice
        voucher_context = invoice.invoice_pay_customer()['context']
        voucher = self.VoucherObj.with_context(voucher_context).create({
            'journal_id': self.bank_journal.id,
            'account_id': self.bank_journal.default_credit_account_id.id,
        })
        voucher.button_proforma_voucher()

        self.assertEqual(self.partner_company.credit, 2300.0, "Credit information inaccurate")
