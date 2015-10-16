# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2014 credativ Ltd (<http://credativ.co.uk>).
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
    "name": "Delivery order date",
    "description":
        """
        Scheduled time of delivery orders automatically sets expected date of stock moves to its value. Also makes expected date of stock moves invisible for delivery orders, so that it can only be modified through the delivery order itself
        """,
    "version": "1.0",
    "author" : "credativ Ltd",
    "website" : "http://credativ.co.uk",
    "category" : "",
    "depends" : [
        "stock",
        ],
    "update_xml" : [
       "stock_picking_view.xml"
        ],
    "data" : [

        ],
    "auto_install": False,
}
