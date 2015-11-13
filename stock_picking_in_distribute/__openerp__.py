# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 credativ Ltd (<http://credativ.co.uk>).
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
    "name": "Incoming shipment redistribution",
    "description":
        """
        Adds option to receive and distribute to internal locations when
        receiving an incoming shipment.
        """,
    "version": "1.0",
    "author": "credativ Ltd",
    "website": "http://www.credativ.co.uk",
    "category": "",
    "depends": [
        "stock",
        ],
    "update_xml": [
       "wizard/stock_picking_in_distribute_wizard_view.xml",
       "stock_view.xml",
        ],
    "data": [
        ],
    "auto_install": False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
