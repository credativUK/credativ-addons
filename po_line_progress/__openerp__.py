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

{'name': 'Purchase order line progress',
 'version': '1.0',
 'category': 'Purchase',
 'author': 'credativ Ltd',
 'website': 'http://www.credativ.co.uk',
 'license': 'AGPL-3',
 'description': """
Show progress of purchase order line
====================================

This module shows the amount of stock transferred for each order line, marking
it as red while partially received.

The percentage of goods received will show as a progressbar if the module
web_progressbar_custom is installed.
""",
 'depends': [
     'purchase',
 ],
 'data': [
     'purchase_view.xml',
 ],
 'installable': True,
}
