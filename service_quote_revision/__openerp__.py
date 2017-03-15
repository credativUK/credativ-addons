# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2017 credativ (http://www.credativ.co.uk). All Rights Reserved
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
##############################################################################{
{
    'name': 'Service Quote Revisions',
    'version': '1.0',
    'category': "Generic Modules/Service Quotations",
    'description':
        """
        This Module creates the copy of service quote on revisions and displays all the edits on the original quote.
        """,
    'author': 'credativ Ltd',
    'website' : 'http://credativ.co.uk',
    'depends': ['pc_service_quotation','pc_contracts'],
    'init_xml': [],
    'update_xml': ['service_quotation_view.xml',
                   'sq_workflow.xml'],
    'demo_xml': [],
    'installable': True,
    'active': False,
    'certificate': '',
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
