# -*- coding: utf-8 -*-
# (c) 2016 credativ ltd. - Ondřej Kuzník
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    'name': 'Serial number on sale orders',
    'summary': 'Set the serial number on sale order line',
    'version': '9.0.1.0.0',
    'category': 'Generic Modules/Inventory Control',
    'author': 'credativ ltd., '
              'Odoo Community Association (OCA)',
    'license': 'AGPL-3',
    'depends': [
        'sale_stock',
    ],
    'data': [
        'views/procurement_view.xml',
        'views/sale_order.xml',
    ],
}
