# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2014 credativ Ltd (<http://credativ.co.uk>).
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
        'name' : 'Auto-Set Sales Team on Sale Orders',
        'version' : '0.1',
        'author' : 'credativ Ltd',
        'description' : """
This module causes the 'Sales Team' field on Sale Orders to be set automatically
based on the corresponding partner whenever the partner is set or changed.
        """,
        'website' : 'http://credativ.co.uk',
        'depends' : [
            'sale_crm',
            ],
        'init_xml' : [
            ],
        'update_xml' : [
            ],
        'installable' : False,
        'active' : False,
}
