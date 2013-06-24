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
from tools.misc import DEFAULT_SERVER_DATETIME_FORMAT
import time
import traceback
import ast
import logging

_logger = logging.getLogger(__name__)
_logger.setLevel(logging.WARNING)

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
            ondelete='cascade',
            help='This is the model on which the action to be managed is defined.'),
        'action_method': fields.char(
            'Action',
            size=128,
            required=True,
            help='This is the name of the method which defines the action to be managed. Typically, such methods begin "action_".'),
        'commencement_state': fields.char(
            'Commencement state',
            size=64,
            help='The resource on which the deferred action is running will have its state changed to this value when the deferred action starts.'),
        'exception_state': fields.char(
            'Exception state',
            size=64,
            help='The resource on which the deferred action is running will have its state changed to this value if any phase of the deferred action fails.'),
        'completion_state': fields.char(
            'Completion state',
            size=64,
            help='The resource on which the deferred action is running will have its state changed to this value once all the phases have completed successfully.'),
        'start_message': fields.text(
            'Start message',
            help='This text is displayed in a dialoge box when the action is initiated. Please use this message to advise the user that the action is being carried out in the background and, if you have configured it, that email notification will follow once the action has completed.'),
        'max_queue_size': fields.integer(
            'Maximum queue size',
            help='Determines the maximum number of instances of this action that may be put in the queue for processing.'),
        'queue_limit_message': fields.text(
            'Queue limit message',
            help='This text is displayed if a user attempts to start a deferred action when the maximum number of queued actions are already in progress.'),
        'max_retries': fields.integer(
            'Maximum retry attempts',
            help='Determines how many times this deferred action will be retried if failures are encountered.'),
        'phases': fields.one2many(
            'deferred.action.phase',
            'deferred_action_id',
            string='Phases',
            help='The phases of a deferred action define the procedure that must be carried out in order to perform the action. Each phase is independently loggable and reportable and may be implemented as a wrapper around a model class method, a stored Python code object, or another deferred action.'),
        'instances': fields.one2many(
            'deferred.action.instance',
            'deferred_action_id',
            string='Instances',
            readonly=True,
            help='Shows current and past instances of this deferred action in use.'),
    }

    _defaults = {
        'max_queue_size': 1,
    }

    def update_model_action(self, cr, uid, ids, context=None):
        '''
        Alters 'model'.'action_method' associated action record to call
        this deferred action instead.
        '''
        raise NotImplementedError('This automatic remapping of action buttons is not implemented. Please alter your action buttons manually.')

    def action_wrapper(self, cr, uid, ids, res_ids, action_args, context=None):
        '''
        This is the method that is called in place of the action method on
        the model. It creates a new instance of this deferred action
        and starts it.

        @param res_ids (list): a list of ids on the model for which the
        action is to be carried out

        @param action_args (list): a list of arguments to the action
        '''
        if isinstance(ids, (list, tuple)):
            id = ids[0]
        else:
            id = ids

        instance_pool = self.pool.get('deferred.action.instance')

        action = self.browse(cr, uid, id, context=context)

        # FIXME Check for exception-state instance and call retry;
        # possibly dependent on uid?
        failed_instance_ids =\
            instance_pool.search(cr, uid, [('deferred_action_id','=',action.id),
                                           ('start_uid','=',uid),
                                           ('state','=','exception')], context=context)
        if failed_instance_ids:
            instance_pool.retry_failed_resources(cr, uid, failed_instance_ids, context=context)
            return {'warning': {'title': 'Retrying',
                                'message': 'Retrying failed action in background.'}}

        instance_id = instance_pool.create(cr, uid, {'deferred_action_id': action.id,
                                                     'start_uid': uid,
                                                     'action_args': action_args,
                                                     'res_ids': res_ids,
                                                     'start_context': context},
                                           context=context)
        instance_info = {'action_name': action.name,
                         'action_model': action.model.model}
        if instance_id:
            instance_pool.start(cr, uid, instance_id, context=context)
            instance = instance_pool.browse(cr, uid, instance_id, context=context)
            instance_info.update({'start_time': instance.start_time,
                                  'owner_name': instance.start_uid.name,
                                  'owner_email': instance.start_uid.user_email})
            return {'warning': {'title': 'Action started in background',
                                'message': action.start_message and action.start_message % instance_info or\
                                'The action "%(action_name)s" has been started in the background on the model "%(action_model)s".' % instance_info}}
        else:
            return {'warning': {'title': 'Action failed to start',
                                'message': 'The action "%(action_name)s" on the model "%(action_model)s" failed to start in the background.' % instance_info}}

deferred_action()


class deferred_action_phase(osv.osv):
    '''
    This model represents a phase of a deferred action. Phases are
    executed in sequence and may also be iterable. Each phase can log
    its activity and report via email to users.
    '''
    _name = 'deferred.action.phase'
    _description = 'A phase in a deferred action procedure'
    _order = 'id, sequence'

    def _check_step_size(self, cr, uid, ids, context=None):
        '''
        Implements constraint to ensure that step_size is >1.
        '''
        for phase in self.browse(cr, uid, ids, context=context):
            if phase.step_size < 1:
                return False
        return True

    def _make_cron_task_name(self, cr, uid, vals, context=None):
        '''
        Construct a consistent, unique name for the cron task to be used
        for this phase. Allows reliable comparison between phases and
        cron entries.
        '''

        return '%(model)s.%(action_method)s.%(usage)s' % vals

    def _get_cron_task(self, cr, uid, ids, context=None):
        if isinstance(ids, (list, tuple)):
            id = ids[0]
        else:
            id = ids

        phase = self.browse(cr, uid, id, context=context)

        cron_task = phase.cron_id
        if not cron_task:
            raise osv.except_osv('Deferred action phase error',
                                 'The phase "%s" of the deferred action "%s" on the model "%s" does not have an associated cron task. '
                                 'A cron entry should have been created when the phase was created.' %\
                                 (phase.id, phase.deferred_action_id.name, phase.deferred_action_id.model.model))

        return cron_task

    def _get_instance(self, cr, uid, ids, states, action_instance_id, context=None):
        if isinstance(ids, (list, tuple)):
            id = ids[0]
        else:
            id = ids

        phase = self.browse(cr, uid, id, context=context)

        phase_instance_pool = self.pool.get('deferred.action.phase.instance')

        phase_instance_ids = phase_instance_pool.search(cr, uid, [('phase_id','=',phase.id),
                                                                  ('action_instance_id','=',action_instance_id),
                                                                  ('state','in',states)],
                                                        context=context)
        if len(phase_instance_ids) > 1:
            raise osv.except_osv('Integrity Error',
                                 'Found multiple phase instances for phase "%s" (in "%s" state) of deferred action "%s" (instance #%s) on model "%s"' %\
                                 (phase.id, states, phase.deferred_action_id.name, action_instance_id, phase.deferred_action_id.model.model))

        return phase_instance_pool.browse(cr, uid, phase_instance_ids[0], context=context)

    def _exec_proc(self, cr, uid, ids, action_instance_id, res_ids, context=None):
        '''
        Executes the procedure for this phase and returns the result and
        some flags in a dict.
        '''
        if isinstance(ids, (list, tuple)):
            id = ids[0]
        else:
            id = ids

        res = {}
        phase = self.browse(cr, uid, id, context=context)

        context['deferred_action'] = True
        context['deferred_action_id'] = phase.deferred_action_id.id
        context['deferred_action_phase_id'] = phase.id
        context['deferred_action_instance_id'] = action_instance_id

        if phase.proc_type == 'method':
            model = self.pool.get(phase.deferred_action_id.model)
            if not model:
                raise osv.except_osv('No such model "%s"' % (phase.deferred_action_id.model.model,),
                                     'The deferred action "%s" attempted to call the method %s on %s, but this model does not exist.' %\
                                     (phase.deferred_action_id.name, phase.deferred_action_id.model.model, phase.method))

            if not hasattr(model, phase.method):
                raise osv.except_osv('No such method "%s.%s"' % (phase.deferred_action_id.model, phase.method),
                                     'The deferred action "%s" attempted to call the method %s on %s, but this method does not exist.' %\
                                     (phase.deferred_action_id.name, phase.deferred_action_id.model.model, phase.method))
            method = getattr(model, phase.method)
            try:
                res['res'] = method(model, cr, uid, res_ids, context=context)
                res['completed'] = True
            except Exception:
                res['completed'] = False
                res['error'] = traceback.format_exc()
                # FIXME What if only some resources fail?

        elif phase.proc_type == 'fnct':
            try:
                ns = {'res_ids': res_ids, 'context': context}
                fnct = compile(phase.proc_fnct)
                exec fnct in ns
                res['res'] = ns['res']
            except Exception:
                res['completed'] = False
                res['error'] = traceback.format_exc()
        elif phase.proc_type == 'action':
            # FIXME Implement this
            raise NotImplementedError('Deferred action phase sub-deferred action not implemented.')

        return res

    def _verify_proc(self, cr, uid, ids, action_instance_id, proc_res, context=None):
        '''
        Executes the verification method to check the result of the procedure.
        '''
        if isinstance(ids, (list, tuple)):
            id = ids[0]
        else:
            id = ids

        res = {}
        phase = self.browse(cr, uid, id, context=context)

        if phase.verify_type == 'method':
            model = self.pool.get(phase.deferred_action_id.model)
            if not model:
                raise osv.except_osv('No such model "%s"' % (phase.deferred_action_id.model.model,),
                                     'The deferred action "%s" verification attempted to call the method %s on %s, but this model does not exist.' %\
                                     (phase.deferred_action_id.name, phase.deferred_action_id.model.model, phase.method))

            if not hasattr(model, phase.method):
                raise osv.except_osv('No such method "%s.%s"' % (phase.deferred_action_id.model.model, phase.method),
                                     'The deferred action "%s" verification attempted to call the method %s on %s, but this method does not exist.' %\
                                     (phase.deferred_action_id.name, phase.deferred_action_id.model.model, phase.method))

            verify_method = getattr(model, phase.verify_method)
            res['success'] = verify_method(model, cr, uid, proc_res, context=context)

        elif phase.verify_type == 'fnct':
            try:
                ns = {'proc_res': proc_res, 'context': context}
                fnct = compile(phase.verify_fnct)
                exec fnct in ns
                res = ns['res']
            except Exception:
                res = {'success': False,
                       'message': 'Verification function failed:\n\n%s' % (traceback.format_exc(),)}
        elif phase.verify_type == 'none':
            # FIXME Implement this
            raise NotImplementedError('Deferred action phase verification sub-deferred action not implemented.')

        return res

    def _notify_owner(self, cr, uid, ids, action_instance_id, res, context=None):
        '''
        Sends email notification to the owner of the deferred action
        indicating the success of failure of this phase.
        '''
        if isinstance(ids, (list, tuple)):
            id = ids[0]
        else:
            id = ids

        phase = self.browse(cr, uid, id, context=context)

        if res['completed'] and res['success'] and phase.notify_success:
            self.pool.get('poweremail.templates').generate_mail(cr, uid, phase.notify_success, phase.id, context=context)
        if (not res['completed'] or not res['success']) and phase.notify_failure:
            context.update({'completed': res['completed'], 'success': res['success']})
            self.pool.get('poweremail.templates').generate_mail(cr, uid, phase.notify_failure, phase.id, context=context)

        return True

    def _do_phase(self, cr, uid, ids, action_instance_id, res_ids, context=None):
        '''
        This method is executed by the scheduler and is responsible for
        executing the phase's procedure, carrying out the
        verification, and processing the notification.
        '''
        res = {}

        for phase in self.browse(cr, uid, ids, context=context):
            # find the resources which will be consumed by the
            # execution of this phase
            if phase.usage == 'iteration' and phase.step_size:
                next_res_ids = res_ids[:phase.step_size]
            else:
                next_res_ids = res_ids

            # execute the phase's procedure; this will return the
            # result, a completed flag, and possibly a stack trace
            res[phase.id] = self._exec_proc(cr, uid, phase.id, next_res_ids, context=context)

            if res[phase.id]['completed']:
                # verify the procedure's result
                res[phase.id].update(self._verify_proc(cr, uid, phase.id, action_instance_id, res[phase.id]['res'], context=context))
            else:
                # if the phase did not complete, it cannot succeed.
                res[phase.id]['success'] = False

            # update the phase instance state
            phase_instance_pool = self.pool.get('deferred.action.phase.instance')
            instance_id = phase_instance_pool.search(cr, uid, [('action_instance_id','=',action_instance_id),
                                                               ('phase_id','=',phase.id)], context=context)
            phase_instance_pool.write(cr, uid, instance_id, {'state': 'finished'}, context=context)

            # store any failed resources
            if not res[phase.id]['success']:
                log_pool = self.pool.get('deferred.action.failed.resource')
                for r in next_res_ids:
                    log_pool.create(cr, uid, {'phase_id': phase.id,
                                              'action_instance_id': action_instance_id,
                                              'res_id': r,
                                              'failure_time': time.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                                              'traceback': res[phase.id]['error']},
                                    context=context)

                failed_res_ids = next_res_ids

            # notify the owner
            self._notify_owner(cr, uid, phase.id, action_instance_id, res[phase.id], context=context)

            # next action (iteration or next phase)
            remaining_res_ids = []
            if phase.usage == 'iteration' and phase.step_size:
                remaining_res_ids = res_ids[phase.step_size:]
                if remaining_res_ids:
                    if phase.iteration_type == 'scheduled':
                        self.iterate_scheduled(cr, uid, [phase.id], action_instance_id, remaining_res_ids, context=None)
                    elif phase.iteration_type == 'immediate':
                        self.iterate_immediate(cr, uid, [phase.id], action_instance_id, remaining_res_ids, context=None)

            if phase.usage != 'iteration' or not remaining_res_ids:
                # start the next phase, passing on only non-failed
                # resources
                self.next_phase(cr, uid, [phase.id], action_instance_id,
                                res[phase.id]['success'] and res_ids or list(set(res_ids) - set(failed_res_ids)),
                                context=context)

        return res

    _columns = {
        'deferred_action_id': fields.many2one(
            'deferred.action',
            ondelete='cascade',
            string='Deferred action',
            required=True),
        'cron_id': fields.many2one(
            'ir.cron',
            required=True,
            readonly=True,
            ondelete='cascade',
            string='Cron task',
            help='This is the cron task that is used to execute this phase in the background.'),
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
        'iteration_type': fields.selection(
            [('scheduled', 'Scheduled'),
             ('immediate', 'Immediate')],
            string='Iteration type',
            help='For iteration phases, determines whether each repetition should run as a separate scheduled task, or sequentially within a single scheduled task.'),
        'execution': fields.selection(
            [('serial', 'Serial'),
             ('parallel', 'Parallel')],
            string='Execution',
            help='Specify whether this phase should be executed in series with the other phases, or whether it can be executed in parallel.'),
        'description': fields.char(
            'Description',
            size=255,
            required=True,
            help='A description of the work done in this phase.'),
        'step_size': fields.integer(
            'Step size',
            help='For iteration phases, this property determines how many resources will be processed by the iteration step at a time. The default is 1.'),
        'proc_type': fields.selection(
            [('method', 'Method'),
             ('fnct', 'Function'),
             ('action', 'Deferred action')],
            required=True,
            string='Procedure type'),
        'proc_method': fields.char(
            'Procedure',
            size=128,
            help='Use this setting to assign a method on the model as the procedure for this phase.'),
        'proc_fnct': fields.text(
            'Procedure',
            help='Use this setting to define a code fragment to be used as the procedure for this phase. The execution environment for this fragment will include the res_ids being processed and the context. The code should assign a value to a variable called "res".'),
        'proc_action': fields.many2one(
            'deferred.action',
            string='Procedure',
            help='Use this setting to assign another deferred action object as the procedure for this phase.'),
        'verify_type': fields.selection(
            [('none', 'No verification'),
             ('method', 'Method'),
             ('fnct', 'Function')],
            required=True,
            string='Verification type'),
        'verify_method': fields.char(
            'Verification',
            size=128,
            help='Use this setting to assign a method on the model as the verification procedure for this phase. The method should return a dict: {"success": bool, "message": str}.'),
        'verify_fnct': fields.text(
            'Verification',
            help='Use this setting to define a code fragment to be used as the verification procedure for this phase. The execution environment for this fragment will include the result of the phase procedure (proc_res) and the context. The code should assign a dict of the form {"success": bool, "message": str} to a variable called "res".'),
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
        'execution': 'serial',
        'step_size': 1,
        'proc_type': 'method',
        'verify_type': 'none',
    }

    _constraints = [
        (_check_step_size, 'Step size must be greater than or equal to 1.', ['step_size']),
    ]

    def default_get(self, cr, uid, fields, context=None):
        res = super(deferred_action_phase, self).default_get(cr, uid, fields, context=context)

        if not context:
            return res

        if context.get('active_model') == 'deferred.action' and context.get('active_id', False):
            res['deferred_action_id'] = context.get('active_id')

        return res

    def create(self, cr, uid, vals, context=None):
        '''
        Create a new ir.cron entry for this phase.
        '''
        cron_pool = self.pool.get('ir.cron')
        deferred_action_pool = self.pool.get('deferred.action')
        deferred_action = deferred_action_pool.browse(cr, uid, vals['deferred_action_id'], context=context)

        if not deferred_action:
            # FIXME This shouldn't happen
            return False

        cron_name = self._make_cron_task_name(cr, uid, dict([('model', deferred_action.model.model), ('action_method', deferred_action.action_method)] + vals.items()), context=context)
        cron_id = cron_pool.search(cr, uid, [('model','=','deferred.action.phase'),
                                             ('name','=',cron_name)],
                                   context=context)
        import pdb; pdb.set_trace()
        if not cron_id:
            cron_id = cron_pool.create(cr, uid, {'name': cron_name,
                                                 'active': False,
                                                 'user_id': uid, # FIXME Or administrator?
                                                 'interval_number': 1,
                                                 'interval_type': 'minutes',
                                                 'numbercall': 1,
                                                 'doall': False,
                                                 'model': 'deferred.action.phase',
                                                 'function': '_do_phase',
                                                 'args': ()},
                                       context=context)

        vals['cron_id'] = cron_id
        phase_id = super(deferred_action_phase, self).create(cr, uid, vals, context=context)
        return phase_id

    def start(self, cr, uid, ids, action_instance_id, res_ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]

        cron_pool = self.pool.get('ir.cron')
        phase_instance_pool = self.pool.get('deferred.action.phase.instance')
        action_instance_pool = self.pool.get('deferred.action.instance')

        res = {}

        for phase in self.browse(cr, uid, ids, context=context):
            # set the action instance's current_phase
            action_instance_pool.write(cr, uid, action_instance_id, {'current_phase': phase.id}, context=context)

            instance_id =\
                phase_instance_pool.create(cr, uid, {'phase_id': phase.id,
                                                     'action_instance_id': action_instance_id,
                                                     'state': 'started',
                                                     'start_time': time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)},
                                           context=context)

            # activate the cron task associated with this phase and
            # schedule it to call immediately
            cron_task = self._get_cron_task(cr, uid, phase.id, context=context)
            cron_pool.write(cr, uid, [cron_task.id], {'active': True,
                                                      'nextcall': time.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                                                      'args': (phase.id, action_instance_id, res_ids)},
                            context=context)

            res[phase.id] = True

        return res

    def pause(self, cr, uid, ids, action_instance_id, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]

        cron_pool = self.pool.get('ir.cron')
        phase_instance_pool = self.pool.get('deferred.action.phase.instance')

        res = {}

        for phase in self.browse(cr, uid, ids, context=context):
            instance = self._get_instance(cr, uid, phase.id, states=('started',), action_instance_id=action_instance_id, context=context)
            phase_instance_pool.write(cr, uid, instance.id, {'state': 'paused'}, context=context)

            # deactivate the cron task associated with this phase
            cron_task = self._get_cron_task(cr, uid, ids, context=context)
            cron_pool.write(cr, uid, [cron_task.id], {'active': False}, context=context)

            res[phase.id] = True

        return res

    def resume(self, cr, uid, ids, action_instance_id, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]

        cron_pool = self.pool.get('ir.cron')
        phase_instance_pool = self.pool.get('deferred.action.phase.instance')

        res = {}

        for phase in self.browse(cr, uid, ids, context=context):
            instance = self._get_instance(cr, uid, phase.id, states=('paused',), action_instance_id=action_instance_id, context=context)
            phase_instance_pool.write(cr, uid, instance.id, {'state': 'started'}, context=context)

            # re-activate the cron task associated with this phase
            cron_task = self._get_cron_task(cr, uid, ids, context=context)
            cron_pool.write(cr, uid, [cron_task.id], {'active': True,
                                                      'nextcall': time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)},
                            context=context)

            res[phase.id] = True

        return res

    def iterate_scheduled(self, cr, uid, ids, action_instance_id, res_ids, context=None):
        '''
        For iterable phases, alters the cron task to execute again with
        another batch of res_ids. The res_ids supplied to this method
        must be the correct list of IDs for this batch (_do_phase
        arranges for this argument to be correct).
        '''
        if isinstance(ids, (int, long)):
            ids = [ids]

        cron_pool = self.pool.get('ir.cron')

        res = {}

        for phase in self.browse(cr, uid, ids, context=context):
            if phase.usage != 'iteration':
                continue
            if phase.iteration_type != 'scheduled':
                raise osv.except_osv('Programming error',
                                     'iterate_scheduled called on phase with iteration type "%s": "%s"' %\
                                     (phase.iteration_type, phase.id))

            cron_task = self._get_cron_task(cr, uid, phase.id, context=context)

            if cron_task.args == (action_instance_id, res_ids):
                # FIXME Or maybe this should just be considered an
                # error and we should raise an exception?
                _logger.warn('Iteration of phase "%s" of action "%s" has been called with the same arguments as previous iteration.' %\
                             (phase.id, phase.deferred_action_id.name))

            cron_pool.write(cr, uid, [cron_task.id], {'active': True,
                                                      'nextcall': time.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                                                      'args': (phase.id, action_instance_id, res_ids)},
                            context=context)

            res[phase.id] = True

        return res

    def iterate_immediate(self, cr, uid, ids, action_instance_id, res_ids, context=None):
        '''
        For iterable phases, continues processing the next batch of
        res_ids immediately (cf. iterate_scheduled). The res_ids
        supplied to this method must be the correct list of IDs for
        this batch (_do_phase arranges for this argument to be
        correct).
        '''
        if isinstance(ids, (int, long)):
            ids = [ids]

        res = {}

        for phase in self.browse(cr, uid, ids, context=context):
            if phase.usage != 'iteration':
                continue
            if phase.iteration_type != 'immediate':
                raise osv.except_osv('Programming error',
                                     'iterate_immediate called on phase with iteration type "%s": "%s"' %\
                                     (phase.iteration_type, phase.id))

            # this is effectively a recursive call; _do_phase is
            # responsible for recursively calling iterate_immediate,
            # truncating the res_ids list each time, and halting
            # recursion once res_ids is empty
            self._do_phase(cr, uid, [phase.id], action_instance_id, res_ids, context=context)
            res[phase.id] = True

        return res

    def retry(self, cr, uid, ids, action_instance_id, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]

        cron_pool = self.pool.get('ir.cron')
        phase_instance_pool = self.pool.get('deferred.action.phase.instance')

        res = {}

        for phase in self.browse(cr, uid, ids, context=context):
            instance = self._get_instance(cr, uid, phase.id, states=('paused','aborted','finished'), action_instance_id=action_instance_id, context=context)
            phase_instance_pool.write(cr, uid, instance.id, {'state': 'started'}, context=context)

            # re-activate the cron task associated with this phase
            cron_task = self._get_cron_task(cr, uid, ids, context=context)
            cron_pool.write(cr, uid, [cron_task.id], {'active': True,
                                                      'nextcall': time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)},
                            context=context)

            res[phase.id] = True

        return res

    def retry_iteration(self, cr, uid, ids, action_instance_id, res_ids, context=None):
        pass

    def skip(self, cr, uid, ids, action_instance_id, res_ids, context=None):
        res = self.finalise(cr, uid, ids, action_instance_id, context=context)
        res.update(self.next_phase(cr, uid, ids, action_instance_id, res_ids, context=context))
        return res

    def abort(self, cr, uid, ids, action_instance_id, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]

        cron_pool = self.pool.get('ir.cron')
        phase_instance_pool = self.pool.get('deferred.action.phase.instance')
        action_instance_pool = self.pool.get('deferred.action.instance')

        res = {}

        for phase in self.browse(cr, uid, ids, context=context):
            # set the action instance's current_phase
            action_instance_pool.write(cr, uid, action_instance_id, {'current_phase': False}, context=context)

            instance = self._get_instance(cr, uid, phase.id, states=('started','paused'), action_instance_id=action_instance_id, context=context)
            phase_instance_pool.write(cr, uid, instance.id, {'state': 'aborted'}, context=context)

            # deactivate the cron task associated with this phase
            cron_task = self._get_cron_task(cr, uid, ids, context=context)
            cron_pool.write(cr, uid, [cron_task.id], {'active': False,
                                                      'nextcall': time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)},
                            context=context)

            res[phase.id] = True

        return res

    def finalise(self, cr, uid, ids, action_instance_id, context=None):
        '''
        Clean up completed instances.
        '''
        if isinstance(ids, (int, long)):
            ids = [ids]

        phase_instance_pool = self.pool.get('deferred.action.phase.instance')
        action_instance_pool = self.pool.get('deferred.action.instance')

        res = {}
        for phase in self.browse(cr, uid, ids, context=context):
            # set the action instance's current_phase
            action_instance_pool.write(cr, uid, action_instance_id, {'current_phase': False}, context=context)

            instance_ids = phase_instance_pool.search(cr, uid, [('phase_id','=',phase.id),
                                                                ('action_instance_id','=',action_instance_id),
                                                                ('state','in',('finished','aborted'))],
                                                      context=context)
            phase_instance_pool.unlink(cr, uid, instance_ids, context=context)

            res[phase.id] = True

        return res

    def next_phase(self, cr, uid, ids, action_instance_id, res_ids, context=None):
        '''
        Schedules the next phase of the deferred action to be executed by
        calling its start method. The phases executed will be those
        that *follow* the supplied phase IDs in sequence (i.e. the IDs
        argument should be the current phase, and this method will
        work out the next phase). This method also initiates closing
        any actions for which this was the last phase.
        '''
        if isinstance(ids, (int, long)):
            ids = [ids]

        next_phases = []
        finished_phases = []
        finished_actions = {}

        res = {}

        for phase in self.browse(cr, uid, ids, context=context):
            following_phase_ids = self.search(cr, uid, [('deferred_action_id','=',phase.deferred_action_id.id),
                                                        ('sequence','<',phase.sequence)],
                                              limit=1, order='sequence asc', context=context)
            if following_phase_ids:
                next_phases.append(following_phase_ids[0])
                finished_phases.append(phase.id)
            else:
                finished_actions[phase.deferred_action_id.id] = action_instance_id
            res[phase.id] = True

        # finalise these phases
        res.update(self.finalise(cr, uid, finished_phases, action_instance_id, context=context))

        # start the next phases
        res.update(self.start(cr, uid, next_phases, action_instance_id, res_ids, context=context))

        # for any phases which are the last in their action, call the
        # finish method on that action
        if finished_actions:
            action_instance_pool = self.pool.get('deferred.action.instance')
            action_instance_pool.finish(cr, uid, finished_actions.values(), context=context)

        return res

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
    _order = 'start_time desc'

    def _get_action_progress(self, cr, uid, ids, field_name, arg, context=None):
        '''
        Calculate how far through the execution of the phases this action
        instance has progressed.
        '''
        # FIXME To be implemented
        return dict([(instance.id, instance.state in ('draft','started','paused') and 0.0 or 100.0)
                     for instance in self.browse(cr, uid, ids, context=context)])

    _columns = {
        'name': fields.char(
            'Name',
            size=64,
            required=True,
            readonly=True),
        'deferred_action_id': fields.many2one(
            'deferred.action',
            ondelete='cascade',
            string='Deferred action',
            readonly=True),
        'state': fields.selection(
            [('draft', 'Draft'),
             ('started', 'Started'),
             ('paused', 'Paused'),
             ('exception', 'Exception'),
             ('aborted', 'Aborted'),
             ('finished', 'Finished')],
            string='State',
            required=True,
            readonly=True),
        'current_phase': fields.many2one(
            'deferred.action.phase',
            readonly=True,
            string='Current phase',
            help='When the action is active, this field points to the currently executing phase.'),
        'start_uid': fields.many2one(
            'res.users',
            string='Owner',
            required=True,
            readonly=True),
        'action_args': fields.text(
            'Action arguments',
            required=True,
            readonly=True),
        'res_ids': fields.text(
            'Actioned resources',
            required=True,
            readonly=True),
        'start_context': fields.serialized(
            'Context',
            readonly=True),
        'start_time': fields.datetime(
            'Start time',
            readonly=True),
        'end_time': fields.datetime(
            'End time',
            readonly=True),
        'attempts': fields.integer(
            'Attempts',
            readonly=True,
            help='The number of times this action instance has been retried.'),
        'progress': fields.function(
            _get_action_progress,
            store=False,
            method=True,
            string='Progress',
            help='Indicates what proportion of the phases have been completed so far. The accuracy of this progress is dependent on the granularity of the phases that make up the action.'),
        'failure_logs': fields.one2many(
            'deferred.action.failed.resource',
            'action_instance_id',
            string='Failed resources',
            readonly=True,
            help='Log entries for resources which have failed to be processed successfully.'),
    }

    _defaults = {
        'name': lambda self, cr, uid, ctx: self.pool.get('ir.sequence').next_by_code(cr, uid, 'deferred.action.instance'),
        'state': 'draft',
    }

    def create(self, cr, uid, vals, context=None):
        '''
        Ensure that no more than max_queue_size instances of this action
        are on the queue already.
        '''
        deferred_action_pool = self.pool.get('deferred.action')
        deferred_action = deferred_action_pool.browse(cr, uid, vals['deferred_action_id'], context=context)

        queued = self.search(cr, uid, [('deferred_action_id','=',deferred_action.id),
                                       ('state','in',['draft','started','paused'])],
                             order='start_time DESC', context=context)
        if len(queued) >= deferred_action.max_queue_size:
            recent_instance = self.browse(cr, uid, queued[0], context=context)
            limit_info = {'action_name': deferred_action.name,
                          'queue_size': len(queued),
                          'queue_limit': deferred_action.max_queue_size,
                          'recent_owner_name': recent_instance.start_uid.name,
                          'recent_start_time': recent_instance.start_time}
            raise osv.except_osv('Integrity error',
                                 deferred_action.queue_limit_message and deferred_action.queue_limit_message % limit_info or
                                 'The deferred action "%(action_name)s" has %(queue_size)s active instances. Only %(queue_limit)s instance(s) should be active at a time.' % limit_info)
        else:
            return super(deferred_action_instance, self).create(cr, uid, vals, context=context)

    def start(self, cr, uid, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]

        phase_pool = self.pool.get('deferred.action.phase')

        res = {}

        for instance in self.browse(cr, uid, ids, context=context):
            if instance.state == 'draft':
                first_phase = instance.deferred_action_id.phases[0]
                # note: phase start method schedules the phase to
                # start and returns immediately
                res[instance.id] = all(phase_pool.start(cr, uid, [first_phase.id], action_instance_id=instance.id, res_ids=ast.literal_eval(instance.res_ids), context=context).values())
                if res[instance.id]:
                    self.write(cr, uid, instance.id, {'state': 'started',
                                                      'start_time': time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)},
                               context=context)

                    # update the action's model's state
                    if instance.deferred_action_id.commencement_state:
                        model_pool = self.pool.get(instance.deferred_action_id.model.model)
                        model_pool.write(cr, uid, ast.literal_eval(instance.res_ids), {'state': instance.deferred_action_id.commencement_state}, context=context)
                else:
                    raise osv.except_osv('Operational error',
                                         'The deferred action "%s" failed to start.' %\
                                         (instance.deferred_action_id.name,))

        return res

    def pause(self, cr, uid, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]

        phase_pool = self.pool.get('deferred.action.phase')

        res = {}

        for instance in self.browse(cr, uid, ids, context=context):
            if instance.state == 'started':
                active_phase_id = instance.current_phase.id
                res[instance.id] = phase_pool.pause(cr, uid, active_phase_id, instance.id, context=context)
                if res[instance.id]:
                    self.write(cr, uid, instance.id, {'state': 'paused'}, context=context)

        return res

    def resume(self, cr, uid, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]

        phase_pool = self.pool.get('deferred.action.phase')

        res = {}

        for instance in self.browse(cr, uid, ids, context=context):
            if instance.state == 'paused':
                active_phase_id = instance.current_phase.id
                res[instance.id] = phase_pool.resume(cr, uid, active_phase_id, instance.id, context=context)
                if res[instance.id]:
                    self.write(cr, uid, instance.id, {'state': 'started'}, context=context)

        return res

    def retry_entire(self, cr, uid, ids, context=None):
        '''
        Re-execute the whole instance, all phases and all resources.
        '''
        if isinstance(ids, (int, long)):
            ids = [ids]

        phase_pool = self.pool.get('deferred.action.phase')

        res = {}

        for instance in self.browse(cr, uid, ids, context=context):
            if instance.attempts <= instance.deferred_action_id.max_retries:
                first_phase = instance.deferred_action_id.phases[0]
                res[instance.id] = all(phase_pool.start(cr, instance.start_uid, [first_phase.id], action_instance_id=instance.id,
                                                        res_ids=ast.literal_eval(instance.res_ids), context=instance.start_context).values())
                if res[instance.id]:
                    self.write(cr, uid, instance.id, {'state': 'started',
                                                      'start_time': time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)},
                               context=context)

                    # update the action's model's state
                    if instance.deferred_action_id.commencement_state:
                        model_pool = self.pool.get(instance.deferred_action_id.model.model)
                        model_pool.write(cr, uid, ast.literal_eval(instance.res_ids), {'state': instance.deferred_action_id.commencement_state}, context=context)
                else:
                    raise osv.except_osv('Operational error',
                                         'The deferred action "%s" failed to start.' %\
                                         (instance.deferred_action_id.name,))
                
                self.write(cr, uid, instance.id, {'attempts': instance.attempts + 1}, context=context)

        return res

    def retry_failed_resources(self, cr, uid, ids, context=None):
        '''
        Re-execute all phases; process only those resources in the
        corresponding deferred.action.failed.resource records.
        '''
        if isinstance(ids, (int, long)):
            ids = [ids]

        phase_pool = self.pool.get('deferred.action.phase')
        log_pool = self.pool.get('deferred.action.failed.resource')

        res = {}

        for instance in self.browse(cr, uid, ids, context=context):
            # find the failed resources
            failed_ids = log_pool.search(cr, uid, [('action_instance_id','=',instance.action_instance_id),
                                                   ('phase_id','=',instance.id)],
                                         context=context)
            failed_res_ids = [l['res_id'] for l in log_pool.read(cr, uid, failed_ids, ['res_id'], context=context)]

            if failed_res_ids and instance.attempts <= instance.deferred_action_id.max_retries:
                # remove the failure logs
                log_pool.unlink(cr, uid, failed_ids, context=context)

                first_phase = instance.deferred_action_id.phases[0]
                res[instance.id] = all(phase_pool.start(cr, instance.start_uid, [first_phase.id], action_instance_id=instance.id,
                                                        res_ids=failed_res_ids, context=instance.start_context).values())
                if res[instance.id]:
                    self.write(cr, uid, instance.id, {'state': 'started',
                                                      'start_time': time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)},
                               context=context)

                    # update the action's model's state
                    if instance.deferred_action_id.commencement_state:
                        model_pool = self.pool.get(instance.deferred_action_id.model.model)
                        model_pool.write(cr, uid, failed_res_ids, {'state': instance.deferred_action_id.commencement_state}, context=context)
                else:
                    raise osv.except_osv('Operational error',
                                         'The deferred action "%s" failed to start.' %\
                                         (instance.deferred_action_id.name,))
                
                self.write(cr, uid, instance.id, {'attempts': instance.attempts + 1}, context=context)

        return res

    def abort(self, cr, uid, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]

        phase_pool = self.pool.get('deferred.action.phase')

        res = {}

        for instance in self.browse(cr, uid, ids, context=context):
            if instance.state in ['started','paused']:
                active_phase_id = instance.current_phase.id
                res[instance.id] = phase_pool.abort(cr, uid, active_phase_id, instance.id, context=context)
                if res[instance.id]:
                    self.write(cr, uid, instance.id, {'state': 'aborted'}, context=context)

        return res

    def finish(self, cr, uid, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]

        res = {}

        for instance in self.browse(cr, uid, ids, context=context):
            if instance.state == 'started':
                # FIXME Consider adding an integrity to check to
                # ensure that all the phases have been executed and
                # that all the res_ids have been consumed.

                # update the action's model's state
                if instance.deferred_action_id.completion_state:
                    model_pool = self.pool.get(instance.deferred_action_id.model.model)
                    model_pool.write(cr, uid, ast.literal_eval(instance.res_ids), {'state': instance.deferred_action_id.completion_state}, context=context)

                self.write(cr, uid, instance.id, {'state': 'finished'}, context=context)
                res[instance.id] = True

        return res

deferred_action_instance()


class deferred_action_phase_instance(osv.osv):
    '''
    Represents an instance of a deferred.action.phase in execution.
    '''
    _name = 'deferred.action.phase.instance'
    _description = 'An instance of a deferred.action.phase in execution'

    _columns = {
        'phase_id': fields.many2one(
            'deferred.action.phase',
            required=True,
            ondelete='cascade',
            string='Deferred action phase'),
        'action_instance_id': fields.many2one(
            'deferred.action.instance',
            required=True,
            ondelete='cascade',
            string='Deferred action instance',
            help='Points to the deferred action instance in which this phase instance is running.'),
        'state': fields.selection(
            [('init', 'Initialised'),
             ('started', 'Started'),
             ('paused', 'Paused'),
             ('aborted', 'Aborted'),
             ('finished', 'Finished')],
            string='State',
            required=True,
            readonly=True),
        'start_time': fields.datetime(
            'Start time',
            readonly=True),
        'end_time': fields.datetime(
            'End time',
            readonly=True),
    }

    _defaults = {
        'state': 'init'
    }

deferred_action_phase_instance()


class deferred_action_failed_resource(osv.osv):
    '''
    Represents a resource for which a deferred action phase resulted
    in failure.
    '''
    _name = 'deferred.action.failed.resource'
    _description = 'Deferred action failed resources'

    def _get_res_name(self, cr, uid, ids, field_name, arg, context=None):
        if not ids:
            return {}
        if isinstance(ids, (int, long)):
            ids = [ids]
        if len(ids) == 1:
            # deal with the case where only one resource name is
            # requested separately
            log = self.browse(cr, uid, ids[0], context=context)
            model_pool = self.pool.get(log.action_instance_id.deferred_action_id.model)
            if model_pool:
                res = model_pool.search(cr, uid, [('id','=',log.res_id)], context=context)
                return {ids[0]: res.name or False}
            else:
                return {ids[0]: False}

        # in this case, multiple resource names are requested, but
        # they are still only ever from one model
        log = self.browse(cr, uid, ids[0], context=context)
        model_pool = self.pool.get(log.action_instance_id.deferred_action_id.model)
        if model_pool:
            res_ids = self.read(cr, uid, ids, ['id','res_id'], context=context)
            resources = model_pool.read(cr, uid, [r['res_id'] for r in res_ids], ['id','name'], context=context)
            res = {}
            for r in res_ids:
                try:
                    res[r['id']] = filter(lambda s: s['id'] == r['res_id'], resources)[0]['name']
                except (IndexError, AttributeError):
                    res[r['id']] = False

            return res
        else:
            return dict([(id, False) for id in ids])
            
    _columns = {
        'phase_id': fields.many2one(
            'deferred.action.phase',
            required=True,
            ondelete='cascade',
            string='Deferred action phase'),
        'action_instance_id': fields.many2one(
            'deferred.action.instance',
            required=True,
            ondelete='cascade',
            string='Deferred action instance',
            help='Points to the deferred action instance in which the phase instance is running.'),
        'res_id': fields.integer(
            'Resource',
            required=True,
            readonly=True,
            help='The ID of the resource which failed'),
        'res_name': fields.function(
            _get_res_name,
            store=False,
            method=True,
            string='Resource name'),
        'failure_time': fields.datetime(
            'Failure time',
            required=True,
            readonly=True),
        'traceback': fields.text(
            'Traceback',
            required=True,
            readonly=True)
    }


deferred_action_failed_resource()
