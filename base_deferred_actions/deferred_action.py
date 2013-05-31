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
        'phases': fields.one2many(
            'deferred.action.phase',
            'deferred_action_id',
            string='Phases',
            help='The phases of a deferred action define the procedure that must be carried out in order to perform the action. Each phase is independently loggable and reportable and may be implemented as a wrapper around a model class method, a stored Python code object, or another deferred action.'),
    }

deferred_action()


class deferred_action_phase(osv.osv):
    '''
    This model represents a phase of a deferred action. Phases are
    executed in sequence and may also be iterable. Each phase can log
    its activity and report via email to users.
    '''
    _name = 'deferred.action.phase'
    _description = 'A phase in a deferred action procedure'

    def _check_step_size(self, cr, uid, ids, context=None):
        '''
        Implements constraint to ensure that step_size is >1.
        '''
        for phase in self.browse(cr, uid, ids, context=context):
            if phase.step_size < 1:
                return False
        return True

    _columns = {
        'name': fields.char(
            'Name',
            size=64,
            required=True),
        'deferred_action_id': fields.many2one(
            'deferred.action',
            required=True),
        'sequence': fields.integer(
            'Sequence',
            help='Use this setting to define the order in which phases of a deferred action are executed.'),
        'usage': fields.selection(
            [('initialisation', 'Initialisation'),
             ('iteration', 'Iteration'),
             ('finalisation', 'Finalisation'),
             ('other', 'Other')],
            string='Usage',
            help='Use this setting to define the purpose of this phase within the deferred action. Phases defined as "iteration" can be repeated for a list of resources.'),
        'description': fields.char(
            'Description',
            size=255,
            required=True,
            help='A description of the work done in this phase.'),
        'step_size': fields.integer(
            'Step size',
            required=True,
            help='For iteration phases, this property determines how many resources will be processed by the iteration step at a time. The default is 1.'),
        'proc_type': fields.selection(
            [('method', 'Method',
              'fnct', 'Function',
              'action', 'Deferred action')],
            required=True,
            string='Procedure type'),
        'proc_method': fields.char(
            'Procedure',
            size=128,
            help='Use this setting to assign a method on the model as the procedure for this phase.'),
        'proc_fnct': fields.text(
            'Procedure',
            help='Use this setting to define a function to be used as the procedure for this phase.'),
        'proc_action': fields.many2one(
            'deferred.action',
            string='Procedure',
            help='Use this setting to assign another deferred action object as the procedure for this phase.'),
        'verify_type': fields.selection(
            [('none', 'No verification',
              'method', 'Method',
              'function', 'Function')],
            required=True,
            string='Verification type'),
        'verify_method': fields.char(
            'Initialisation verification',
            size=128,
            help='Use this setting to assign a method on the model as the verification procedure for this phase. The method should return a dict: {"success": bool, "message": str}.'),
        'verify_fnct': fields.text(
            'Initialisation verification',
            help='Use this setting to define a function to be used as the verification procedure for this phase. The function should return a dict: {"success": bool, "message": str}.'),
        'notify_success': fields.many2one(
            'poweremail.templates',
            string='Success email',
            help='An email template to send when this phase completes successfully.'),
        'notify_fail': fields.many2one(
            'poweremail.templates',
            string='Fail email',
            help='An email template to send when this phase fails.'),
        }

    _defaults = {
        'step_size': 1,
        'proc_type': 'method',
        'verify_type': 'none',
    }

    _constraints = [
        (_check_step_size, 'Step size must be greater than or equal to 1.', ['step_size']),
    ]

    def start(self, cr, uid, ids, res_ids, context=None):
        pass

    def iterate(self, cr, uid, ids, res_ids, context=None):
        pass

    def retry(self, cr, uid, ids, res_ids, context=None):
        pass

    def skip(self, cr, uid, ids, res_ids, context=None):
        pass

deferred_action_phase()


class deferred_action_instance(osv.osv):
    '''
    This model represents an instance of a deferred action being
    executed. It has a many2one relation with
    deferred.action. Resources in this model effectively define the
    queue for the deferred action.
    '''
    _name = 'deferred.action.instance'
    _description = 'An executing workflow action'

    _columns = {
        'name': fields.char(
            'Name',
            size=64,
            required=True,
            readonly=True),
        'deferred_action_id': fields.many2one(
            'deferred.action',
            string='Deferred action'),
        'state': fields.selection(
            [('draft', 'Draft'),
             ('started', 'Started'),
             ('paused', 'Paused'),
             ('aborted', 'Aborted'),
             ('finished', 'Finished')],
            string='State',
            required=True,
            readonly=True),
        'start_uid': fields.many2one(
            'res.users',
            string='Owner',
            required=True,
            readonly=True),
        'action_args': fields.serialized(
            'Action arguments',
            required=True,
            readonly=True),
        'start_time': fields.datetime(
            'Start time',
            required=True,
            readonly=True),
        'end_time': fields.datetime(
            'End time',
            readonly=True),
        
    }

    _defaults = {
        'name': lambda self, cr, uid, ctx: self.pool.get('ir.sequence').next_by_code(cr, uid, 'deferred.action.instance'),
    }

    def start(self, cr, uid, ids, context=None):
        pass

    def retry(self, cr, uid, ids, context=None):
        pass

    def stop(self, cr, uid, ids, context=None):
        pass

deferred_action_instance()
