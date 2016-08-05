# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2016 credativ ltd (<http://www.credativ.co.uk>). All Rights Reserved
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
        'name' : 'Purchase Automatic Invoice',
        'version' : '7.0.1.0',
        'author' : 'credativ Ltd',
        'description' : '''
Allows invoices to be automatically created for purchase orders
''',
        'website' : 'http://credativ.co.uk',
        'depends' : [
            'purchase',
            'stock',
            ],
        'init_xml' : [
            ],
        'update_xml' : [
            'partner_view.xml',
            'purchase_data.xml',
            ],
        'installable' : True,
        'active' : False,
}
