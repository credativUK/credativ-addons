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
_logger.setLevel(logging.DEBUG)

class deferred_action(osv.osv):
    '''
    This model is used to manage long-running workflow actions.
    '''
    _name = 'deferred.action'
    _description = 'Manage a long-running workflow action'

    def _message(self, cr, uid, ids, title=None, message=None, context=None):
        '''
        This method uses the deferred.action.notification wizard to
        display notifications to users when deferred actions are
        started.
        '''
        if not title and not message:
            return False
        title = title or 'Deferred action notification'

        notify_pool = self.pool.get('deferred.action.notification')

        notify_id = notify_pool.create(cr, uid, {'title': title, 'message': message}, context=context)

        return {'name': title,
                'view_type': 'form',
                'view_mode': 'form,tree',
                'res_model': 'deferred.action.notification',
                'view_id': False,
                'res_id': notify_id,
                'target': 'new',
                'type': 'ir.actions.act_window'}

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

        # Check for exception-state instance and call retry
        failed_instance_ids =\
            instance_pool.search(cr, uid, [('deferred_action_id','=',action.id),
                                           ('start_uid','=',uid),
                                           ('state','=','exception')], context=context)
        if failed_instance_ids:
            instance_pool.retry_failed_resources(cr, uid, failed_instance_ids, context=context)
            return self._message(cr, uid, id,
                                 title='Retrying',
                                 message='Retrying failed action in background.',
                                 context=context)

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
            return self._message(cr, uid, id,
                                 title='Action started in background',
                                 message=action.start_message and action.start_message % instance_info or\
                                 'The action "%(action_name)s" has been started in the background on the model "%(action_model)s".' % instance_info,
                                 context=context)
        else:
            return self._message(cr, uid, id,
                                 title='Action failed to start',
                                 message='The action "%(action_name)s" on the model "%(action_model)s" failed to start in the background.' % instance_info,
                                 context=context)

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

    def _get_name(self, cr, uid, ids, field_name, arg, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        return dict([(phase.id, '%d: %s' % (phase.sequence, phase.description))
                     for phase in self.browse(cr, uid, ids, context=context)])

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

        return phase_instance_pool.browse(cr, uid, phase_instance_ids and phase_instance_ids[0] or False, context=context)

    def _exec_proc(self, cr, uid, ids, action_instance_id, res_ids, context=None):
        '''
        Executes the procedure for this phase and returns the result,
        possibly an new list of res_ids, and some flags in a dict.

        @param res_ids (int): the IDs of the resources on which the
        procedure should be executed
        '''
        if isinstance(ids, (list, tuple)):
            id = ids[0]
        else:
            id = ids

        res = {}
        phase = self.browse(cr, uid, id, context=context)

        action_instance_pool = self.pool.get('deferred.action.instance')
        action_instance = action_instance_pool.browse(cr, uid, action_instance_id, context=context)

        context['deferred_action'] = True
        context['deferred_action_model'] = phase.deferred_action_id.model.model
        context['deferred_action_res_ids'] = ast.literal_eval(action_instance.res_ids)
        context['deferred_action_id'] = phase.deferred_action_id.id
        context['deferred_action_phase_id'] = phase.id
        context['deferred_action_instance_id'] = action_instance_id

        if phase.proc_type == 'method':
            model_name = phase.proc_model and phase.proc_model.model or phase.deferred_action_id.model.model
            model = self.pool.get(model_name)
            if not model:
                raise osv.except_osv('No such model "%s"' % (model_name,),
                                     'The deferred action "%s" attempted to call the method %s on %s, but this model does not exist.' %\
                                     (phase.deferred_action_id.name, phase.proc_method, model_name))

            if not hasattr(model, phase.proc_method):
                raise osv.except_osv('No such method "%s.%s"' % (phase.deferred_action_id.model, phase.proc_method),
                                     'The deferred action "%s" attempted to call the method %s on %s, but this method does not exist.' %\
                                     (phase.deferred_action_id.name, phase.proc_method, model_name))

            method = getattr(model, phase.proc_method)
            # the method should have been decorated to initiate the
            # deferred action; but now we need to call the original
            # method; at decoration time, this was stored in the
            # orig_action property
            if not hasattr(method, 'orig_action'):
                _logger.warn('The deferred action "%s" attempted to call the method %s on %s, but this method does not have an orig_action property. '
                             'It may not have been decorated with @defer_action.' %\
                             (phase.deferred_action_id.name, phase.proc_method, model_name))
            method = getattr(method, 'orig_action', method)

            try:
                # the method may be unbound (for decorated action
                # methods where the stored orig_action method is
                # applied) or bound (for phase methods)
                if not hasattr(method, 'im_self') or method.im_self is None:
                    res['res'] = method(self=model, cr=cr, uid=uid, ids=res_ids, context=context)
                else:
                    res['res'] = method(cr=cr, uid=uid, ids=res_ids, context=context)
                for s in ['next_res_ids', 'context']:
                    if s in res['res']:
                        res[s] = res['res'].pop(s)
                res['completed'] = True
            except Exception:
                res['completed'] = False
                res['error'] = traceback.format_exc()
                _logger.debug('_exec_proc caught exception:\n%s\n' % (res['error'],))

        elif phase.proc_type == 'fnct':
            try:
                ns = {'model': model_name, 'res_ids': res_ids, 'context': context}
                fnct = compile(phase.proc_fnct)
                exec fnct in ns
                res['res'] = ns['res']
                for s in ['next_res_ids', 'context']:
                    if s in ns:
                        res[s] = ns[s]
                res['completed'] = True
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
            model_name = phase.verify_model and phase.verify_model.model or phase.deferred_action_id.model.model
            model = self.pool.get(model_name)
            if not model:
                raise osv.except_osv('No such model "%s"' % (model_name,),
                                     'The deferred action "%s" verification attempted to call the method %s on %s, but this model does not exist.' %\
                                     (phase.deferred_action_id.name, phase.verify_method, model_name))

            if not hasattr(model, phase.verify_method):
                raise osv.except_osv('No such method "%s.%s"' % (model_name, phase.verify_method),
                                     'The deferred action "%s" verification attempted to call the method %s on %s, but this method does not exist.' %\
                                     (phase.deferred_action_id.name, phase.verify_method, model_name))

            verify_method = getattr(model, phase.verify_method)
            res = verify_method(cr, uid, proc_res, context=context)

        elif phase.verify_type == 'fnct':
            try:
                ns = {'proc_res': proc_res, 'context': context}
                fnct = compile(phase.verify_fnct)
                exec fnct in ns
                res = ns['res']
            except Exception:
                res = {'success': False,
                       'message': 'Verification function failed:\n\n%s' % (traceback.format_exc(),)}

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
        if (not res['completed'] or not res['success']) and phase.notify_fail:
            context.update({'completed': res['completed'], 'success': res['success']})
            self.pool.get('poweremail.templates').generate_mail(cr, uid, phase.notify_fail, phase.id, context=context)

        return True

    def _do_phase(self, cr, uid, ids, action_instance_id, res_ids, context=None):
        '''
        This method is executed by the scheduler and is responsible for
        executing the phase's procedure, carrying out the
        verification, and processing the notification.
        '''
        if isinstance(ids, (int, long)):
            ids = [ids]

        res = {}

        for phase in self.browse(cr, uid, ids, context=context):
            # find the resources which will be consumed by the
            # execution of this phase
            if phase.usage == 'iteration' and phase.step_size:
                next_res_ids = res_ids[:phase.step_size]
            else:
                next_res_ids = res_ids

            # execute the phase's procedure; this will return a dict
            # keyed by resource ID where each value is either some
            # returned resource or a dict with the key 'error'
            # containing an exception object
            res[phase.id] = self._exec_proc(cr, uid, phase.id, action_instance_id, next_res_ids, context=context)

            _logger.debug('Procedure returned: %s' % (res[phase.id],))

            if res[phase.id]['completed']:
                # There are two types of failure: 'errored' resources
                # are those for which the executed procedure signaled
                # an error; 'failed' resources are those which
                # completed successfully but failed the verification
                # procedure (applied below)

                # find the errored resources
                res[phase.id]['errored'] = dict([(r_id, d)
                                                 for r_id, d in res[phase.id]['res']['res'].items()
                                                 if isinstance(d, dict) and 'error' in d])
                for i in res[phase.id]['errored'].keys():
                    res[phase.id]['res']['res'].pop(i)

                # verify the results of the successfully completed
                # resources
                res[phase.id].update(self._verify_proc(cr, uid, phase.id, action_instance_id, res[phase.id]['res'], context=context))

                # ensure the success flag is True only if no errored
                # resources exist and the verification procedure set
                # it to True
                res[phase.id]['success'] = res[phase.id].get('success', True) and not res[phase.id]['errored']
            else:
                # if the phase did not complete, it cannot succeed.
                res[phase.id]['success'] = False

            _logger.debug('Procedure result after verification: %s' % (res[phase.id],))

            # store any errored or failed resources
            if not res[phase.id]['success']:
                log_pool = self.pool.get('deferred.action.failed.resource')

                for r_id, d in res[phase.id].get('errored', {}).items():
                    log_pool.create(cr, uid, {'phase_id': phase.id,
                                              'action_instance_id': action_instance_id,
                                              'model_name': phase.proc_model and phase.proc_model.model or phase.deferred_action_id.model.model,
                                              'res_id': r_id,
                                              'failure_time': time.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                                              'traceback': str(d.get('error', Exception('Unknown error')))},
                                    context=context)

                for r in res[phase.id].get('failed_ids', []):
                    log_pool.create(cr, uid, {'phase_id': phase.id,
                                              'action_instance_id': action_instance_id,
                                              'model_name': phase.proc_model and phase.proc_model.model or phase.deferred_action_id.model.model,
                                              'res_id': r,
                                              'failure_time': time.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                                              'traceback': 'Failed verification test.'},
                                    context=context)

            # check for iteration
            remaining_res_ids = []
            if phase.usage == 'iteration' and phase.step_size:
                remaining_res_ids = res_ids[phase.step_size:]
                if remaining_res_ids:
                    if phase.iteration_type == 'scheduled':
                        self.iterate_scheduled(cr, uid, [phase.id], action_instance_id, remaining_res_ids, context=context)
                    elif phase.iteration_type == 'immediate':
                        self.iterate_immediate(cr, uid, [phase.id], action_instance_id, remaining_res_ids, context=context)

            # next action
            if phase.usage != 'iteration' or not remaining_res_ids:
                # update the phase instance state
                action_instance_pool = self.pool.get('deferred.action.instance')
                phase_instance_pool = self.pool.get('deferred.action.phase.instance')
                instance_id = phase_instance_pool.search(cr, uid, [('action_instance_id','=',action_instance_id),
                                                                   ('phase_id','=',phase.id)], context=context)
                if res[phase.id].get('errored', False) or res[phase.id].get('failed_ids', False):
                    phase_instance_pool.action_fail(cr, uid, instance_id, context=context)
                    action_instance_pool.exception(cr, uid, action_instance_id, reason=res[phase.id].get('error'), context=context)
                elif not res[phase.id]['success']:
                    phase_instance_pool.action_abort(cr, uid, instance_id, context=context)
                    # also abort the action instance
                    action_instance_pool.abort(cr, uid, action_instance_id, reason=res[phase.id].get('error'), context=context)
                else:
                    phase_instance_pool.action_finish(cr, uid, instance_id, context=context)

                # notify the owner
                self._notify_owner(cr, uid, phase.id, action_instance_id, res[phase.id], context=context)

                # if the procedure returned success=False but there
                # are no errored or failed resources, we abort the
                # phase and action instances; so prevent the next
                # phase from executing
                if not res[phase.id]['success'] and\
                   not res[phase.id].get('errored', False) and not res[phase.id].get('failed_ids', False):
                    continue

                # update the context used to execute phases with
                # anything returned by the previous phase
                if res[phase.id].get('context'):
                    action_instance = action_instance_pool.browse(cr, uid, action_instance_id, context=context)
                    start_context = action_instance.start_context
                    start_context.update(res[phase.id]['context'])
                    action_instance_pool.write(cr, uid, action_instance_id, {'start_context': start_context}, context=context)

                # start the next phase, passing on only non-failed
                # resources from the res_ids processed by this phase
                # for the action_res_ids argument, and the res_ids
                # that the phase procedure returned as to be processed
                # next for the phase_res_ids argument
                if res[phase.id]['success']:
                    if 'next_res_ids' in res[phase.id] and res[phase.id]['next_res_ids'] is None:
                        # if the phase procedure set 'next_res_ids' to
                        # None, it means use the originally actioned
                        # resources
                        action_res_ids = ast.literal_eval(action_instance_pool.read(cr, uid, action_instance_id, ['res_ids'], context=context)['res_ids'])
                        phase_res_ids = None
                    else:
                        action_res_ids = res_ids
                        phase_res_ids = res[phase.id].get('next_res_ids')
                else:
                    action_res_ids = list(set(res_ids) - set(res[phase.id].get('errored', {}).keys() +\
                                                             res[phase.id].get('failed_ids', [])))
                    phase_res_ids = None

                self.next_phase(cr, uid, [phase.id], action_instance_id, action_res_ids, phase_res_ids, context=context)

        return res

    _columns = {
        'name': fields.function(
            _get_name,
            type='char',
            readonly=True,
            method=True,
            string='Name'),
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
        'proc_model': fields.many2one(
            'ir.model',
            string='Procedure model',
            help='This is the model on which the phase method is defined.'),
        'proc_method': fields.char(
            'Procedure',
            size=128,
            help='Use this setting to assign a method on the model as the procedure for this phase. The method should return a dict containing keys "res" and optioanlly "next_res_ids" (which should be a list of IDs on to be processed by the next phase) and "context". The value of "res" should be a dict keyed with the res_ids of each resource processed. The values for each key may be a dict including an "error" key which should contain an exception object.'),
        'proc_fnct': fields.text(
            'Procedure',
            help='Use this setting to define a code fragment to be used as the procedure for this phase. The execution environment for this fragment will include the res_ids being processed, the name of the model from which those res_ids are taken, and the context. The code should assign a value to a variable called "res". It may also assign a value to a variable called "next_res_ids" which should be a list of IDs to be processed by the next phase and to "context". The value of "res" should be a dict keyed with the res_ids of each resource processed. The values for each key may be a dict including an "error" key which should contain an exception object.'),
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
        'verify_model': fields.many2one(
            'ir.model',
            string='Verification model',
            help='This is the model on which the verification method is defined.'),
        'verify_method': fields.char(
            'Verification',
            size=128,
            help='Use this setting to assign a method on the model as the verification procedure for this phase. The method should return a dict: {"success": bool, "message": str, "failed_ids": list}.'),
        'verify_fnct': fields.text(
            'Verification',
            help='Use this setting to define a code fragment to be used as the verification procedure for this phase. The execution environment for this fragment will include the result of the phase procedure (proc_res) and the context. The code should assign a dict of the form {"success": bool, "message": str, "failed_ids": list} to a variable called "res".'),
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

    def start(self, cr, uid, ids, action_instance_id, action_res_ids, phase_res_ids=None, context=None):
        '''
        Starts a phase. Creates a new deferred.action.phase.instance for
        the phase and activates the cron task for this phase,
        assigning it the appropriate res_ids and context for its
        'args'.

        @param action_instance_id (int): the ID of the
        deferred.action.instance in which this phase is running

        @param action_res_ids (list of int): the IDs of the
        resources from deferred.action.model for which this deferred
        action is being executed

        @param phase_res_ids (list of int): the IDs of the resources
        which should be processed by this phase; this allows phases to
        work on resources different to those for which the
        deferred.action was started
        '''
        if isinstance(ids, (int, long)):
            ids = [ids]

        cron_pool = self.pool.get('ir.cron')
        phase_instance_pool = self.pool.get('deferred.action.phase.instance')
        action_instance_pool = self.pool.get('deferred.action.instance')

        res = {}

        for phase in self.browse(cr, uid, ids, context=context):
            _logger.debug('Starting phase %s; action_res_ids = %s; phase_res_ids = %s' % (phase.id,action_res_ids, phase_res_ids))
            # set the action instance's current_phase
            action_instance_pool.write(cr, uid, action_instance_id, {'current_phase': phase.id}, context=context)

            instance_id =\
                phase_instance_pool.create(cr, uid, {'phase_id': phase.id,
                                                     'action_instance_id': action_instance_id,
                                                     'res_ids': phase_res_ids or action_res_ids,
                                                     'state': 'started',
                                                     'start_time': time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)},
                                           context=context)

            # activate the cron task associated with this phase and
            # schedule it to call immediately
            action_instance = action_instance_pool.browse(cr, uid, action_instance_id, context=context)
            cron_task = self._get_cron_task(cr, uid, phase.id, context=context)
            args = (phase.id, action_instance_id,
                    phase_res_ids or action_res_ids,
                    action_instance.start_context)
            _logger.debug('Setting phase %d args: %s' % (phase.id, args))
            cron_pool.write(cr, uid, [cron_task.id], {'active': True,
                                                      'numbercall': 1,
                                                      'nextcall': time.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                                                      'args': args},
                            context=context)
            action_instance_pool.write(cr, uid, action_instance_id, {'action_args': args}, context=context)

            res[phase.id] = True

        return res

    def pause(self, cr, uid, ids, action_instance_id, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]

        cron_pool = self.pool.get('ir.cron')
        phase_instance_pool = self.pool.get('deferred.action.phase.instance')

        res = {}

        for phase in self.browse(cr, uid, ids, context=context):
            _logger.debug('Pausing phase %s' % (phase.id,))
            instance = self._get_instance(cr, uid, phase.id, states=('started',), action_instance_id=action_instance_id, context=context)
            if instance:
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
            _logger.debug('Resuming phase %s' % (phase.id,))
            instance = self._get_instance(cr, uid, phase.id, states=('paused',), action_instance_id=action_instance_id, context=context)
            if instance:
                phase_instance_pool.action_start(cr, uid, instance.id, context=context)

            # re-activate the cron task associated with this phase
            cron_task = self._get_cron_task(cr, uid, ids, context=context)
            cron_pool.write(cr, uid, [cron_task.id], {'active': True,
                                                      'numbercall': 1,
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
        action_instance_pool = self.pool.get('deferred.action.instance')

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

            _logger.debug('Iterating phase %s for res_ids %s' % (phase.id, res_ids))
            action_instance = action_instance_pool.browse(cr, uid, action_instance_id, context=context)
            args = (phase.id, action_instance_id, res_ids, action_instance.start_context)
            _logger.debug('Setting phase %d args: %s' % (phase.id, args))
            cron_pool.write(cr, uid, [cron_task.id], {'active': True,
                                                      'numbercall': 1,
                                                      'nextcall': time.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                                                      'args': args},
                            context=context)
            action_instance_pool.write(cr, uid, action_instance_id, {'action_args': args}, context=context)

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

        action_instance_pool = self.pool.get('deferred.action.instance')

        res = {}

        for phase in self.browse(cr, uid, ids, context=context):
            if phase.usage != 'iteration':
                continue
            if phase.iteration_type != 'immediate':
                raise osv.except_osv('Programming error',
                                     'iterate_immediate called on phase with iteration type "%s": "%s"' %\
                                     (phase.iteration_type, phase.id))

            _logger.debug('Iterating phase %s recursively for res_ids %s' % (phase.id, res_ids))
            # this is effectively a recursive call; _do_phase is
            # responsible for recursively calling iterate_immediate,
            # truncating the res_ids list each time, and halting
            # recursion once res_ids is empty
            action_instance = action_instance_pool.browse(cr, uid, action_instance_id, context=context)
            self._do_phase(cr, uid, [phase.id], action_instance_id, res_ids, context=action_instance.start_context)
            res[phase.id] = True

        return res

    def retry_entire(self, cr, uid, ids, action_instance_id, context=None):
        '''
        Retry the phase for all resources.
        '''
        if isinstance(ids, (int, long)):
            ids = [ids]

        cron_pool = self.pool.get('ir.cron')
        phase_instance_pool = self.pool.get('deferred.action.phase.instance')

        res = {}

        for phase in self.browse(cr, uid, ids, context=context):
            _logger.debug('Retying phase %s for all resources' % (phase.id,))
            instance = self._get_instance(cr, uid, phase.id, states=('paused','aborted','failed','finished'), action_instance_id=action_instance_id, context=context)
            if instance:
                phase_instance_pool.action_retry(cr, uid, instance.id, context=context)

            # re-activate the cron task associated with this phase
            cron_task = self._get_cron_task(cr, uid, ids, context=context)
            cron_pool.write(cr, uid, [cron_task.id], {'active': True,
                                                      'numbercall': 1,
                                                      'nextcall': time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)},
                            context=context)

            res[phase.id] = True

        return res

    def retry_failed_resources(self, cr, uid, ids, action_instance_id, context=None):
        '''
        Retry the phase but only for the resources in the fail log.
        '''
        if isinstance(ids, (int, long)):
            ids = [ids]

        cron_pool = self.pool.get('ir.cron')
        phase_instance_pool = self.pool.get('deferred.action.phase.instance')
        action_instance_pool = self.pool.get('deferred.action.instance')
        log_pool = self.pool.get('deferred.action.failed.resource')

        res = {}

        for phase in self.browse(cr, uid, ids, context=context):
            _logger.debug('Retrying phase %s for failed resources only' % (phase.id,))
            instance = self._get_instance(cr, uid, phase.id, states=('paused','aborted','failed','finished'), action_instance_id=action_instance_id, context=context)
            if instance:
                phase_instance_pool.action_start(cr, uid, instance.id, context=context)

            failed_ids = log_pool.search(cr, uid, [('action_instance_id','=',action_instance_id),
                                                   ('phase_id','=',phase.id)],
                                         context=context)
            # construct a dict grouping the failed res_ids by their model
            failed_res_ids = {}
            for l in log_pool.read(cr, uid, failed_ids, ['model_name', 'res_id'], context=context):
                if l['model_name'] in failed_res_ids:
                    failed_res_ids[l['model_name']].append(l['res_id'])
                else:
                    failed_res_ids[l['model_name']] = [l['res_id']]

            if failed_res_ids:
                # we'll only schedule IDs from one model
                if len(failed_res_ids) > 1:
                    raise osv.except_osv('Integrity error',
                                         'Cannot retry phase with fail logs for multiple models: %s' % (failed_res_ids.keys(),))

                cron_task = self._get_cron_task(cr, uid, phase.id, context=context)

                action_instance = action_instance_pool.browse(cr, uid, action_instance_id, context=context)
                args = (phase.id,
                        action_instance_id,
                        failed_res_ids.get(failed_res_ids.keys()[0], []),
                        action_instance.start_context)
                _logger.debug('Setting phase %d args: %s' % (phase.id, args))
                cron_pool.write(cr, uid, [cron_task.id], {'active': True,
                                                          'numbercall': 1,
                                                          'nextcall': time.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                                                          'args': args},
                                context=context)
                action_instance_pool.write(cr, uid, action_instance_id, {'action_args': args}, context=context)

                # remove the failure logs
                log_pool.unlink(cr, uid, failed_ids, context=context)
            else:
                # if there were no failed resources for this phase,
                # ensure that the next phase gets called
                self.next_phase(cr, uid, [phase.id], action_instance_id, action_res_ids=None, phase_res_ids=None, retrying=True, context=context)

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
            _logger.debug('Aborting phase %s' % (phase.id,))
            # set the action instance's current_phase
            action_instance_pool.write(cr, uid, action_instance_id, {'current_phase': False}, context=context)

            instance = self._get_instance(cr, uid, phase.id, states=('started','paused','exception'), action_instance_id=action_instance_id, context=context)
            if instance:
                phase_instance_pool.action_abort(cr, uid, instance.id, context=context)

            # deactivate the cron task associated with this phase
            cron_task = self._get_cron_task(cr, uid, ids, context=context)
            cron_pool.write(cr, uid, [cron_task.id], {'active': False,
                                                      'numbercall': 1,
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
            _logger.debug('Finalising phase %s' % (phase.id,))
            # set the action instance's current_phase
            action_instance_pool.write(cr, uid, action_instance_id, {'current_phase': False}, context=context)

            finished_instance_ids =\
                phase_instance_pool.search(cr, uid, [('phase_id','=',phase.id),
                                                     ('action_instance_id','=',action_instance_id),
                                                     ('state','in',('finished','aborted'))],
                                           context=context)
            phase_instance_pool.unlink(cr, uid, finished_instance_ids, context=context)

            # failed_instance_ids =\
            #     phase_instance_pool.search(cr, uid, [('phase_id','=',phase.id),
            #                                          ('action_instance_id','=',action_instance_id),
            #                                          ('state','in',('failed',))],
            #                                context=context)

            res[phase.id] = True

        return res

    def next_phase(self, cr, uid, ids, action_instance_id, action_res_ids, phase_res_ids=None, retrying=False, context=None):
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
        finished_actions = {}
        log_pool = self.pool.get('deferred.action.failed.resource')
        action_instance_pool = self.pool.get('deferred.action.instance')

        res = {}

        # if no resources are supplied, halt execution of the action
        # by not advancing to the next phase
        if not action_res_ids and not phase_res_ids and not retrying:
            _logger.debug('Phase %s called next_phase with no resources; halting action instance %s' % (ids, action_instance_id))
            return res

        for phase in self.browse(cr, uid, ids, context=context):
            following_phase_ids = self.search(cr, uid, [('deferred_action_id','=',phase.deferred_action_id.id),
                                                        ('sequence','>',phase.sequence)],
                                              limit=1, order='sequence asc', context=context)
            if following_phase_ids:
                next_phases.append(following_phase_ids[0])
            else:
                finished_actions[phase.deferred_action_id.id] = action_instance_id
            res[phase.id] = True

        # finalise these phases
        _logger.debug('Transition from phase %s: finalising phases: %s' % (ids, ids))
        res.update(self.finalise(cr, uid, ids, action_instance_id, context=context))

        # start (or retry) the next phases
        if next_phases:
            failed_ids = log_pool.search(cr, uid, [('action_instance_id','=',action_instance_id),
                                                   ('phase_id','=',next_phases[0])],
                                         context=context)
            if not failed_ids and not retrying:
                _logger.debug('Transition from phase %s: starting phases: %s; action_res_ids=%s; phase_res_ids=%s' % (ids, next_phases, action_res_ids, phase_res_ids))
                res.update(self.start(cr, uid, next_phases, action_instance_id, action_res_ids, phase_res_ids, context=context))
            else:
                _logger.debug('Transition from phase %s: retrying phase: %s' % (ids, next_phases[0]))
                res.update(self.retry_failed_resources(cr, uid, next_phases[0], action_instance_id, context=context))

        # for any phases which are the last in their action, call the
        # finish method on that action
        if finished_actions:
            _logger.debug('Transition from phase %s: finishing actions: %s' % (ids, finished_actions.values()))
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
        res = {}
        for instance in self.browse(cr, uid, ids, context=context):
            if instance.state == 'draft':
                res[instance.id] = 0.0
            elif instance.state in ('started','retrying','paused','exception','aborted'):
                if instance.current_phase:
                    res[instance.id] = 100.0 * (float(instance.current_phase.sequence) / (max([phase.sequence for phase in instance.deferred_action_id.phases]) + 1.0))
                elif instance.failure_logs:
                    res[instance.id] = 100.0 * (float(max([log.phase_id.sequence for log in instance.failure_logs])) / (max([phase.sequence for phase in instance.deferred_action_id.phases]) + 1.0))
                else:
                    res[instance.id] = 50.0
            elif instance.state == 'finished':
                res[instance.id] = 100.0

        return res

        return dict([(instance.id, instance.state in ('draft','started','paused') and 0.0 or 100.0)
                     for instance in self.browse(cr, uid, ids, context=context)])

    def _get_attempts_progress(self, cr, uid, ids, field_name, arg, context=None):
        return dict([(instance.id, 100.0 * (float(instance.attempts) / (instance.deferred_action_id.max_retries or instance.attempts or 1.0)))
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
             ('retrying', 'Retrying'),
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
        'attempts_progress': fields.function(
            _get_attempts_progress,
            type='float',
            store=False,
            method=True,
            string='Attempts',
            help='Shows how many of the available retry attempts have been used.'),
        'status_message': fields.text(
            'Current state',
            readonly=True),
        'progress': fields.function(
            _get_action_progress,
            type='float',
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

    def button_reset_attempts(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'attempts': 0}, context=context)

    def create(self, cr, uid, vals, context=None):
        '''
        Ensure that no more than max_queue_size instances of this action
        are on the queue already.
        '''
        deferred_action_pool = self.pool.get('deferred.action')
        deferred_action = deferred_action_pool.browse(cr, uid, vals['deferred_action_id'], context=context)

        queued = self.search(cr, uid, [('deferred_action_id','=',deferred_action.id),
                                       ('state','in',['draft','started','paused','retrying'])],
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
                res[instance.id] = all(phase_pool.start(cr, uid, [first_phase.id], action_instance_id=instance.id, action_res_ids=ast.literal_eval(instance.res_ids), context=context).values())
                if res[instance.id]:
                    self.write(cr, uid, instance.id, {'state': 'started',
                                                      'start_time': time.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                                                      'status_message': False},
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
        log_pool = self.pool.get('deferred.action.failed.resource')

        res = {}

        for instance in self.browse(cr, uid, ids, context=context):
            if not instance.deferred_action_id.max_retries or instance.attempts <= instance.deferred_action_id.max_retries:
                # first remove the failure logs that triggered this retry
                failed_ids = log_pool.search(cr, uid, [('action_instance_id','=',instance.id)],
                                             context=context)
                log_pool.unlink(cr, uid, failed_ids, context=context)

                first_phase = instance.deferred_action_id.phases[0]
                res[instance.id] = all(phase_pool.retry_entire(cr, instance.start_uid.id, [first_phase.id], action_instance_id=instance.id,
                                                               action_res_ids=ast.literal_eval(instance.res_ids), context=instance.start_context).values())
                if res[instance.id]:
                    self.write(cr, uid, instance.id, {'state': 'retrying',
                                                      'start_time': time.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                                                      'end_time': False},
                               context=context)

                    # update the action's model's state
                    if instance.deferred_action_id.commencement_state:
                        model_pool = self.pool.get(instance.deferred_action_id.model.model)
                        model_pool.write(cr, uid, ast.literal_eval(instance.res_ids), {'state': instance.deferred_action_id.commencement_state}, context=context)
                else:
                    raise osv.except_osv('Operational error',
                                         'The deferred action "%s" failed to restart.' %\
                                         (instance.deferred_action_id.name,))
                
                self.write(cr, uid, instance.id, {'attempts': instance.attempts + 1}, context=context)
            else:
                raise osv.except_osv('Action error',
                                     'The deferred action "%s" has reached its maximum number of retry attempts.' %\
                                     (instance.deferred_action_id.name,))

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
            failed_ids = log_pool.search(cr, uid, [('action_instance_id','=',instance.id)],
                                         context=context)
            # construct a dict grouping the failed res_ids by their model
            failed_res_ids = {}
            for l in log_pool.read(cr, uid, failed_ids, ['model_name', 'res_id'], context=context):
                if l['model_name'] in failed_res_ids:
                    failed_res_ids[l['model_name']].append(l['res_id'])
                else:
                    failed_res_ids[l['model_name']] = [l['res_id']]

            if failed_res_ids and (not instance.deferred_action_id.max_retries or instance.attempts <= instance.deferred_action_id.max_retries):
                first_phase = instance.deferred_action_id.phases[0]
                res[instance.id] = all(phase_pool.retry_failed_resources(cr, instance.start_uid.id, [first_phase.id], action_instance_id=instance.id,
                                                                         context=instance.start_context).values())
                if res[instance.id]:
                    self.write(cr, uid, instance.id, {'state': 'retrying',
                                                      'start_time': time.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                                                      'end_time': False},
                               context=context)

                    # update the action's model's state
                    if instance.deferred_action_id.commencement_state:
                        model_pool = self.pool.get(instance.deferred_action_id.model.model)
                        # FIXME We don't actually know which of the
                        # original action resources failed
                        model_pool.write(cr, uid, ast.literal_eval(instance.res_ids),
                                         {'state': instance.deferred_action_id.commencement_state}, context=context)
                else:
                    raise osv.except_osv('Operational error',
                                         'The deferred action "%s" failed to start.' %\
                                         (instance.deferred_action_id.name,))
                
                self.write(cr, uid, instance.id, {'attempts': instance.attempts + 1}, context=context)
            else:
                raise osv.except_osv('Action error',
                                     'The deferred action "%s" has reached its maximum number of retry attempts.' %\
                                     (instance.deferred_action_id.name,))

        return res

    def abort(self, cr, uid, ids, reason=None, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]

        phase_pool = self.pool.get('deferred.action.phase')

        res = {}

        for instance in self.browse(cr, uid, ids, context=context):
            if instance.state in ['started','paused','retrying','exception']:
                active_phase = instance.current_phase
                if active_phase:
                    phase_pool.abort(cr, uid, active_phase.id, instance.id, context=context)

                self.write(cr, uid, instance.id, {'state': 'aborted',
                                                  'end_time': time.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                                                  'status_message': reason or False}, context=context)
                res[instance.id] = True

        return res

    def exception(self, cr, uid, ids, reason=None, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]

        res = {}

        for instance in self.browse(cr, uid, ids, context=context):
            if instance.state in ['started','paused','retrying','exception']:
                self.write(cr, uid, instance.id, {'state': 'exception',
                                                  'status_message': reason or False}, context=context)
                res[instance.id] = True

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

                _logger.debug('deferred.action.instance.finish has been called for %s; setting state to "finished"' % (instance.id,))
                self.write(cr, uid, instance.id, {'state': 'finished',
                                                  'end_time': time.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                                                  'status_message': False}, context=context)
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
             ('retrying', 'Retrying'),
             ('paused', 'Paused'),
             ('aborted', 'Aborted'),
             ('failed', 'Failed'),
             ('finished', 'Finished')],
            string='State',
            required=True,
            readonly=True),
        'res_ids': fields.text(
            'Actioned resources',
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

    def action_init(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'init'}, context=context)

    def action_start(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'started'}, context=context)

    def action_retry(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'retrying'}, context=context)

    def action_pause(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'paused'}, context=context)

    def action_abort(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'aborted',
                                  'end_time': time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)},
                   context=context)

    def action_fail(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'failed',
                                  'end_time': time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)},
                   context=context)

    def action_finish(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'finished',
                                  'end_time': time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)},
                   context=context)

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
            model_pool = self.pool.get(log.model_name or log.action_instance_id.deferred_action_id.model)
            if model_pool:
                res = model_pool.browse(cr, uid, log.res_id, context=context)
                return {ids[0]: '[%s] %s' % (log.res_id, (res and hasattr(res, 'name')) and res.name or '')}
            else:
                return {ids[0]: '[%s]' % (log.res_id,)}

        # in this case, multiple resource names are requested, but
        # they are still only ever from one model
        log = self.browse(cr, uid, ids[0], context=context)
        model_pool = self.pool.get(log.model_name or log.action_instance_id.deferred_action_id.model)
        if model_pool:
            res_ids = self.read(cr, uid, ids, ['id','res_id'], context=context)
            resources = model_pool.read(cr, uid, [r['res_id'] for r in res_ids], ['id','name'], context=context)
            res = {}
            for r in res_ids:
                try:
                    res[r['id']] = '[%s] %s' % (r['res_id'], filter(lambda s: s['id'] == r['res_id'], resources)[0]['name'])
                except (IndexError, AttributeError):
                    res[r['id']] = '[%s]' % (r['res_id'],)

            return res
        else:
            return dict([(id, False) for id in ids])

    def _get_model(self, cr, uid, ids, field_name, arg, context=None):
        if not ids:
            return {}
        if isinstance(ids, (int, long)):
            ids = [ids]

        model_pool = self.pool.get('ir.model')
        res = {}
        for log in self.read(cr, uid, ids, ['id', 'model_name'], context=context):
            model_ids = model_pool.search(cr, uid, [('model','=',log['model_name'])], limit=1, context=context)
            if model_ids:
                res[log['id']] = model_ids[0]
            else:
                res[log['id']] = False
        return res
            
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
        'model_name': fields.char(
            'Model',
            size=128,
            readonly=True,
            help='The model from which the failed resources are taken.'),
        'model': fields.function(
            _get_model,
            type='many2one',
            relation='ir.model',
            store=False,
            method=True,
            readonly=True,
            string='Model',
            help='The model from which the failed resources are taken.'),
        'res_name': fields.function(
            _get_res_name,
            type='char',
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
