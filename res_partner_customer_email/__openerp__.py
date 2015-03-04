# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright 2015 credativ Ltd
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

{'name': 'Automatic email triggered for new customers',
 'version': '1.0.0',
 'category': 'Sales',
 'author': 'credativ Ltd',
 'website': 'http://www.credativ.co.uk',
 'license': 'AGPL-3',
 'description': """
Automatically sends an email when a new customer partner is created who is not set as opt-out.

Note: The condition on the automatic server action is set to False by default. This needs to be changed to True to enable the automatic sending of emails in this case.

* Settings > Technical > Actions > Server Actions
* Server action: "New customer email"
""",
 'depends': [
     'email_template',
 ],
 'data': [
     'res_partner.xml'
 ],
 'installable': True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: