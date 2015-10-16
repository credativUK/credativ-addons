##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 credativ ltd (<http://www.credativ.co.uk>). All Rights Reserved
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
    'name': 'Multiple tiers within partner hierarchy',
    'version':'1.0',
    'category' : 'Sales Management',
    'description': """
This module allows multiple levels in the partner hierarchy by allowing contacts to be added to non-companies.
    """,
    'author' : 'credativ',
    'website' : 'http://www.credativ.co.uk',
    'depends':[
               'base',
               ],
    'update_xml' : [
        'res_partner_view.xml'
    ],
    'auto_install': False,
    'installable': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

