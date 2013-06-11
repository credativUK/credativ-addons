# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution	
#    Copyright (C) 2013 credativ ltd (<http://www.credativ.co.uk>). All Rights Reserved
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
    'name': 'base_deferred_actions',
    'version': '0.1',
    'category': 'Generic Modules/Base',
    'description': """This addon provides facilities for breaking down long running workflow action procedures, running them in the background, reporting on their progress, and re-doing failed parts of them.

It provides the models deferred.action, deferred.action.phase, and deferred.action.instance. deferred.action encpasulates a workflow action method on some model. Each deferred.action may have any number of deferred.action.phases associated with it. These will be executed in order and can also be iterable. Developers will make alterations to an action on a model to break it down into distinct phases and create a new deferred.action.phase record for each of those phases. Each phase may also generate logging and email reporting feedback. A deferred.action.instance represents a deferred.action in progress, implementing a queue of actions and preventing the same action being executed more than once.

Views are included in Settings | Customisation | Deferred Actions for creating, editing, and controlling deferred actions. However, basic deferred actions can be configured just using the decorators provided in deferred_actions_osv.""",
    'author': 'credativ',
    'depends': [
        'base',
        'poweremail',
    ],
    'update_xml': [
        'deferred_action_data.xml',
        'deferred_action_view.xml',
    ],
    'demo_xml': [],
    'installable': True,
    'active': False,
}
