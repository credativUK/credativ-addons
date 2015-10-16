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
##############################################################################

{
    "name": "Invoice Tax with Invoice Currency",
    "version": "1.0",
    'category' : 'Accounting & Finance',
    'description' :"""
Tax in Invoice currency
=================================================
This module create tax entries in invoice currency instead of company currency.

Setup
-----
* Install module
* Go to Accounting/Configuration/Taxes/Taxes
* Check enable_invoice_entry field to enable taxation entries in invoice currency

Usage Scenario
--------------
This module can be use for companies using multi company accounting along with multi currency setup.

E.g
A company based in Spain selling to UK customer. A shop is setup in London selling products in GBP paying 20% VAT to UK GOV.
Setup

* Create new Tax codes 1. UK sales 2. UK VAT 20%
* Create new tax in sysem, viz 20% UK TAX
* Check enable_invoice_entry field on tax form view
* Create new invoice with GBP currency and UK VAT TAX
* Verify taxes appears in GBP amount on tax report

Note: A different UK chart of accounts can be created to manage UK Tax more efficiently.
""",
    'website': 'http://www.credativ.co.uk',
    "depends": ["account"],
    "author": "Credativ",
    'data': ['account_view.xml'],
    'installable': False,
    'auto_install': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
