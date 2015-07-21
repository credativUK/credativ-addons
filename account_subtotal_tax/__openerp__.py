# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution   
#    Copyright (C) 2015 credativ Ltd (<http://credativ.co.uk>).
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
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
{
    "name": "Account Subtotal Tax",
    "description":
        """
The sale order lines, purchase order lines and account
invoice lines will show subtotal including tax

Note that this creates a new field in the view rather
than overriding the existing subtotal field, so this
will not change the behaviour of any reports using the
existing subtotal field without tax.
        """,
    "version": "1.0",
    "author" : "credativ Ltd",
    "website" : "http://credativ.co.uk",
    "category" : "",
    "depends" : [
        "sale",
        "purchase",
        "account",
        ],
    "update_xml" : [
        "sale_view.xml",
        "purchase_view.xml",
        "account_invoice_view.xml",
        ],
    "data" : [],
    "auto_install": False,
}
