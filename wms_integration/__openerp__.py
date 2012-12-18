# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution	
#    Copyright (C) 2012 credativ ltd (<http://www.credativ.co.uk>). All Rights Reserved
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    'name': 'wms_integration',
    'version': '0.1',
    'category': 'Generic Modules/Warehouse',
    'description': """
    Allows data interchange with external warehouse management systems.
    """,
    'author': 'credativ',
    'depends': ['base_external_referentials',
                'stock',
                'stock_dispatch',
                'purchase',
                'sale'],
    'update_xml': ['wms_integration_core_view.xml',
                   'settings/external.referential.type.csv'],
    'demo_xml': [],
    'installable': True,
    'active': False,
}
