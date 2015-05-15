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
        'name' : 'Categories on Products',
        'version' : '0.1',
        'author' : 'credativ Ltd',
        'description' : """
By default, product categories are stored on product templates rather than the products themselves. This module adds the 'Category' field to the product itself - this is particularly useful when used with product variants, in which co-variant products share the same template (thus forcing them to share a category).
        """,
        'website' : 'http://credativ.co.uk',
        'depends' : [
            'product',
            ],
        'init_xml' : [
            ],
        'update_xml' : [
            ],
        'installable' : True,
        'active' : False,
}
