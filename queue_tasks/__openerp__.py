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
        'name' : 'Queue Tasks',
        'version' : '7.0.1.0',
        'author' : 'credativ Ltd',
        'description' : '''
The module allows any function called by the user to be deferred to
run in the background as a connector queue job.
''',
        'website' : 'http://credativ.co.uk',
        'depends' : [
            'connector',
            ],
        'init_xml' : [
            ],
        'update_xml' : [
            'queue_task_view.xml',
            'security/ir.model.access.csv',
            ],
        'installable' : True,
        'active' : False,
}
