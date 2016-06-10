# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2016 credativ ltd (<http://www.credativ.co.uk>). All Rights Reserved
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
        'name' : 'Magento Bundle Availability',
        'version' : '1.0',
        'author' : 'credativ Ltd',
        'description' : '''
Building on the bundle-import functionality provided by 'Magentoerpconnect Bundle Split', this module ensures that moves belonging to a particular bundle are always considered together when testing for availability.
''',
        'website' : 'http://credativ.co.uk',
        'depends' : [
            'magentoerpconnect_bundle_split',
            ],
        'init_xml' : [
            ],
        'update_xml' : [
            ],
        'installable' : True,
        'active' : False,
}
