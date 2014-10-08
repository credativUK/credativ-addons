# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright 2014 credativ Ltd
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

{'name': 'Magento openerp connector - Pricelist synchronize',
 'version': '1.0.0',
 'category': 'Connector',
 'author': 'credativ Ltd',
 'website': 'http://www.credativ.co.uk',
 'license': 'AGPL-3',
 'description': """

MagentoConnector Pricelist
==========================

Overview
--------

    * Sync price from magento based on store view
    * Product type simple are only supported at the moment

Installation
------------
    * Install a module
    * Synchronize products before synchronizing pricelist
    * Open store view Connectors -> Magento -> Storeviews
    * Click Synch pricelist and assign/create pricelist to sync

Extension for Magento OpenERP to faciliate pricelist synchronization. This module provides one way pricelist synchronization to OpenERP
""",
 'depends': [
     'magentoerpconnect',
 ],
 'data': [
     "magento_model_view.xml",
     "magentoconnect_data.xml",
 ],
 'installable': True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: