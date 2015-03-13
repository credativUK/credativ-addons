# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 credativ Ltd (<http://credativ.co.uk>).
#    All Rights Reserved
#    $Id$
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
    'name' : 'Specific Due Date for Payment Terms',
    'version' : '1.0.0',
    'author' : 'credativ',
    'website' : 'http://credativ.co.uk',
    'depends' : [
        'account',
    ],
    'category' : 'Accounting',
    'description': '''
This module allows specific due dates to be used on payment term computation lines.

* If no specific date is selected, the standard logic is used for the payment due date computation

''',
    'init_xml' : [],
    'demo_xml' : [],
    'update_xml' : [
        "account_view.xml",
    ],
    'active': False,
    'installable': True
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
