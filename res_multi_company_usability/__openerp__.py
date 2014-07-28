# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution   
#    Copyright (C) 2014 credativ ltd (<http://www.credativ.co.uk>). All Rights Reserved
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
    'name' : 'Multi Company Usability',
    'version' : '1.0.0',
    'author' : 'credativ',
    'website' : 'http://credativ.co.uk',
    'depends' : [
        'account',
        'stock',
    ],
    'category' : 'Accounting & Finance',
    'description': '''
Modifies the name_get functions of various account objects and prefixes them with the
company name. This makes selection of accounts, fiscal years etc less ambigious when
multiple companies share the same naming scheme.

Note:
* This does not affect name_search at this moment so matching will not work using this format.
* The decision was taken to replace the name_get instead of add to it for performance reasons,
  this may affect compatability with other modules which also affect name_get.
''',
    'init_xml' : [],
    'demo_xml' : [],
    'update_xml' : [],
    'active': True,
    'installable': True,
    'auto_install': False,
    'application': True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
