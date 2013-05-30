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

from osv import osv, fields

class deferred_action(osv.osv):
    '''
    This model is used to manage long-running workflow actions.
    '''
    _name = 'deferred.action'
    _description = 'Manage a long-running workflow action'

    _columns = {
        'name': fields.char(
            'Name',
            size=64,
            required=True),
        'model': fields.many2one(
            'ir.model',
            required=True,
            string='Model',
            help='This is the model on which the action to be managed is defined.'),
        'action_method': fields.char(
            'Action',
            size=128,
            required=True,
            help='This is the name of the method which defines the action to be managed. Typically, such methods begin "action_".'),

        # Settings for the initialise procedure
        'init_proc_type': fields.selection(
            [('method', 'Method',
              'fnct', 'Function',
              'action', 'Deferred action')],
            required=True,
            string='Initialise procedure type'),
        'init_proc_method': fields.char(
            'Initialisation',
            size=128,
            help='Use this setting to assign a method on the model as the action initialisation procedure'),
        'init_proc_fnct': fields.text(
            'Initialisation',
            help='Use this setting to define a function to be used as the action initialisation procedure'),
        'init_proc_action': fields.many2one(
            'deferred.action',
            string='Initialisation',
            help='Use this setting to assign another deferred action object as the action initialisation procedure'),
        'init_verify_type': fields.selection(
            [('none', 'No verification',
              'method', 'Method',
              'function', 'Function')],
            required=True,
            string='Initialisation verification type'),
        'init_verify_method': fields.char(
            'Initialisation verification',
            size=128,
            help='Use this setting to assign a method on the model as the initialisation verification procedure. The method should return a dict: {"success": bool, "message": str}.'),
        'init_verify_fnct': fields.text(
            'Initialisation verification',
            help='Use this setting to define a function to be used as the initialisation verification procedure. The function should return a dict: {"success": bool, "message": str}.'),
        'init_notify_success': fields.many2one(
            'poweremail.template',
            string='Initialisation success email',
            help='An email template to send when the initialisation completes successfully.'),
        'init_notify_fail': fields.many2one(
            'poweremail.template',
            string='Initialisation fail email',
            help='An email template to send when the initialisation fails.'),

        # Settings for the iteration procedure

        # Settings for the finalisation procedure
        'finish_proc_type': fields.selection(
            [('method', 'Method',
              'fnct', 'Function',
              'action', 'Deferred action')],
            required=True,
            string='Initialise procedure type'),
        'finish_proc_method': fields.char(
            'Finalisation',
            size=128,
            help='Use this setting to assign a method on the model as the action finalisation procedure'),
        'finish_proc_fnct': fields.text(
            'Finalisation',
            help='Use this setting to define a function to be used as the action finalisation procedure'),
        'finish_proc_action': fields.many2one(
            'deferred.action',
            string='Finalisation',
            help='Use this setting to assign another deferred action object as the action finalisation procedure'),
        'finish_verify_type': fields.selection(
            [('none', 'No verification',
              'method', 'Method',
              'function', 'Function')],
            required=True,
            string='Finalisation verification type'),
        'finish_verify_method': fields.char(
            'Finalisation verification',
            size=128,
            help='Use this setting to assign a method on the model as the finalisation verification procedure. The method should return a dict: {"success": bool, "message": str}.'),
        'finish_verify_fnct': fields.text(
            'Finalisation verification',
            help='Use this setting to define a function to be used as the finalisation verification procedure. The function should return a dict: {"success": bool, "message": str}.'),
        'finish_notify_success': fields.many2one(
            'poweremail.template',
            string='Finalisation success email',
            help='An email template to send when the finalisation completes successfully.'),
        'finish_notify_fail': fields.many2one(
            'poweremail.template',
            string='Finalisation fail email',
            help='An email template to send when the finalisation fails.'),

    }

    _defaults = {
        'init_proc_type': 'method',
        'init_verify_type': 'none',
        'finish_proc_type': 'method',
        'finish_verify_type': 'none',
    }

deferred_action()


class deferred_action_instance(osv.osv):
    '''
    This model represents an instance of a long-running workflow action
    being executed. It has a many2one relation with deferred.action.
    '''
    _name = 'deferred.action.instance'
    _description = 'An executing workflow action'

    _columns = {
        'name': fields.char(
            'Name',
            size=64,
            required=True),
    }

    _defaults = {
        'name': lambda self, cr, uid, ctx: self.pool.get('ir.sequence').next_by_code(cr, uid, 'deferred.action.instance'),
    }

deferred_action_instance()
