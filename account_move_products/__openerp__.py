# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2014 credativ Ltd (<http://credativ.co.uk>).
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
        'name' : 'Products on Journal Items',
        'version' : '0.1',
        'author' : 'credativ Ltd',
        'description' : '''
This module makes visible the product associated with Journal
Items in their form and tree views, and adds a corresponding
filter and 'Group By' option.
''',
        'website' : 'http://credativ.co.uk',
        'depends' : [
            'account',
            ],
        'init_xml' : [
            ],
        'update_xml' : [
            'account_move_line.xml',
            ],
        'installable' : True,
        'active' : False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
