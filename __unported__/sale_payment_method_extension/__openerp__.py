# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 credativ Ltd (<http://www.credativ.co.uk>).
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
    'name': 'Sale Payment Method Extension',
    'version': '0.0.1',
    'category': 'Connector',
    'license': 'AGPL-3',
    'description': """
Sale Payment Method Extension
===================

This module extends existing module sale_payment_method and adds shop on payment method

This module link payment methods with storeview. When there are multiple shops with different currency,
the sale_payment_method link payment with correct sale order.

Scenario:
### Magento Setup ###
* Europe Website
 * UK store
    * UK store view (GBP)
    * Payment method: Paypal
 * France Store
    * France Store view (EUR)
    * Payment method: Paypal
  * Australia Store
    * Australia Store view (AUD)
    * Payment method: Paypal

### openerp Setup ###
* UK company (Main company)
  * UK shop (Default currency GBP)
  * Euro Shop (EUR)
  * Australia Shop (AUD)
* Sale Payment methods
  * Paypal UK (UK company) - UK Store
  * Paypal EUR (UK company) - France Store
  * Paypal AUD (UK company) - Australia Store


""",
    'author': 'credativ Ltd',
    'website': 'http://www.credativ.co.uk/',
    'depends': ['sale_payment_method',
                ],
    'data': ['payment_method_view.xml',
             ],
    'demo': [],
    'installable': True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
