# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2016 credativ Ltd (<http://credativ.co.uk>).
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
    'name': 'Auto-confirm Trusted Purchase Orders',
    'version': '1.0',
    'category': 'Sales & Purchases',
    'description': """
Adds a scheduled task which will confirm any Purchase Orders
past their specified auto-confirm date if the supplier is
marked as 'trusted', and send an email notification out to
the configured address.
        """,
    'author': 'credativ Ltd',
    'website' : 'http://credativ.co.uk',
    'depends': [
        'purchase',
        'mail',
        'queue_tasks',
    ],
    'init_xml': [
        'purchase_data.xml',
    ],
    'update_xml': [
        'partner_view.xml',
        'purchase_view.xml',
    ],
}
