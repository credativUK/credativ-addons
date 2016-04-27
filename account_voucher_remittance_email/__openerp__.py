# -*- coding: utf-8 -*-
# © 2016 credativ Ltd (http://credativ.co.uk)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Send Remittance Report to Supplier",
    "summary": "Send email to supplier with remittance report attached",
    "version": "8.0.1.0.0",
    "category": "Accounting & Finance",
    "website": "http://credativ.co.uk/",
    "author": "credativ ltd",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "account_voucher_remittance_report",
    ],
    "data": [
        "data/voucher_email_template.xml",
        "views/voucher_payment_receipt_view.xml",
    ],
}
