# -*- coding: utf-8 -*-
# © 2016 credativ Ltd (http://credativ.co.uk)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Voucher Remittance Report",
    "summary": "Add Remittance Advice Report on Voucher",
    "version": "8.0.1.0.0",
    "category": "Accounting & Finance",
    "website": "http://credativ.co.uk/",
    "author": "credativ ltd",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "account_voucher",
    ],
    "data": [
        "views/account_voucher_remittance_report.xml",
        'views/report_voucherremittance.xml'
    ],
}
