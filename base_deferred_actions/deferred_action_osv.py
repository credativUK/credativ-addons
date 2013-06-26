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

'''
This module contains utilities required by developers implementing
deferred actions for their models.

To create a deferred action:

 1) add deferred_action_osv to the inheritance list for your model;

 2) apply the defer_action decorator to the relevant action method
 on your model;

 3) move code from your action method into new methods on your model
 that implement each of the phases of your action and apply the
 action_phase decorator to them; (you may leave your action method
 unaltered to create a single-phase deferred action);

 4) use the deferred actions form (from Settings | Customisation |
 Deferred Actions) to edit the properties of the newly created
 deferred action.
'''

from osv import osv
from openerp import SUPERUSER_ID
import inspect

import logging
_logger = logging.getLogger(__name__)
_logger.setLevel(logging.DEBUG)

def defer_action(single_phase=False, name=None, start_message=None):
    '''
    This is a decorator which is used to mark an action method as
    deferred. It will also attempt to create a new deferred.action
    object if a method is marked as deferred, but an object does not
    already exist.
    '''
    _logger.debug('Defer action decorator called.')
    def wrap(action):
        _logger.debug('Making %s into a deferred action' % (action.__name__,))
        def new_action(self, cr, uid, ids, *args, **kwargs):
            _logger.debug('Calling decorated deferred action on %s' % (str(self),))
            if not 'context' in kwargs:
                kwargs['context'] = {}

            action_pool = self.pool.get('deferred.action')
            deferred_action = self._find_deferred_action(cr, uid, action.__name__, context=kwargs.get('context'))

            if not deferred_action:
                deferred_action = self._create_deferred_action(cr, uid, action_method=action.__name__, name=name, start_message=start_message,
                                                               single_phase=single_phase, context={})

            if not deferred_action.phases:
                raise osv.except_osv('Configuration error',
                                     'This action is marked as deferred, but the corresponding deferred.action object is not fully configured. '
                                     'Please consult your system administrator.\n\nAction: "%s"' % (deferred_action.name,))

            # try and find the context
            candidates = filter(lambda a: isinstance(a, dict) and 'lang' in a, list(args)) +\
                         filter(lambda a: a[0] == 'context' or isinstance(a[1], dict) and 'lang' in a[1], kwargs.items())
            if len(candidates) > 1:
                # if multiple candidates are found, sort them by
                # number of keys; then we'll take the longest one
                candidates.sort(cmp=lambda a, b: cmp(len(b), len(a)))
            ctx = candidates and candidates[0] or {}
            kwargs['context'] = isinstance(ctx, dict) and ctx or ctx[1]

            _logger.debug('Calling deferred action "%s" (ID %s) with args: %s; kwargs: %s; context=%s' %\
                          (deferred_action.name, deferred_action.id, args, kwargs, kwargs.get('context', None)))
            return action_pool.action_wrapper(cr, uid, deferred_action.id, ids, tuple(args), **kwargs)

        new_action.__name__ = action.__name__
        new_action.__doc__ = action.__doc__

        return new_action

    return wrap

def action_phase(action_method, description, sequence=None, usage=None, execution='serial', step_size=None):
    '''
    This is a decorator which is used to mark a model method as an
    action phase.
    '''
    def wrap(method):
        method.phase = None
        method.action_method = action_method
        method.description = description
        method.sequence = sequence
        method.usage = usage
        method.execution = execution
        method.step_size = step_size

        return method

    return wrap

        
class deferred_action_osv(object):#osv.orm.AbstractModel):
    '''
    Add this class to a model class's inheritance list to get utility
    methods for retrieving and creating deferred actions for action
    methods on that model.
    '''
    #_name = 'deferred.action.osv'

    def _get_model_id(self, cr, uid, context=None):
        if hasattr(self, '_model_id'):
            return self._model_id
        else:
            model_pool = self.pool.get('ir.model')
            model_ids = model_pool.search(cr, uid, [('model','=',self._name)], limit=1, context=context)
            if model_ids:
                self._model_id = model_ids[0]
                return self._model_id
            else:
                raise osv.except_osv('Database Error',
                                     'Model "%s" not found in ir.model table.' % (self._name,))

    def _find_deferred_action(self, cr, uid, action_method, context=None):
        action_pool = self.pool.get('deferred.action')
        action_ids = action_pool.search(cr, uid, [('model','=',self._get_model_id(cr, uid, context=context)),
                                                  ('action_method','=',action_method)],
                                        context=context)
        if action_ids:
            return action_pool.browse(cr, uid, action_ids[0], context=context)
        else:
            return None

    def _create_deferred_action(self, cr, uid, action_method, name=None, start_message=None, single_phase=False, context=None):
        action_pool = self.pool.get('deferred.action')
        action = self._find_deferred_action(cr, uid, action_method, context=context)
        if action:
            return action

        action_id = action_pool.create(cr, SUPERUSER_ID, {'name': name or '%s.%s' % (self._name, action_method),
                                                          'model': self._get_model_id(cr, uid, context=context),
                                                          'action_method': action_method,
                                                          'start_message': start_message or False},
                                       context=context)
        if single_phase:
            phase_pool = self.pool.get('deferred.action.phase')
            phase_pool.create(cr, SUPERUSER_ID, {'deferred_action_id': action_id,
                                                 'proc_type': 'method',
                                                 'proc_method': action_method,
                                                 'description': '%s.%s auto-created by deferred_action_osv' % (self._name, action_method),
                                                 'usage': 'other'},
                              context=context)
        else:
            self._create_phases(cr, uid, action_method, context=context)

        return action_pool.browse(cr, uid, action_id, context=context)

    def _find_phases(self, cr, uid, action_method, phase_method=None, context=None):
        deferred_action = self._find_deferred_action(cr, uid, action_method, context=context)

        phase_pool = self.pool.get('deferred.action.phase')
        
        search_args = [('deferred_action_id','=',deferred_action.id),
                       ('proc_type','=','method')]
        if phase_method:
            search_args.append(('proc_method','=',phase_method))

        phase_ids = phase_pool.search(cr, uid, search_args, context=context)
        return phase_pool.browse(cr, uid, phase_ids, context=context)

    def _create_phase(self, cr, uid, action_method, phase_method, description=None, sequence=None, usage=None, execution=None, step_size=None, context=None):
        phases = self._find_phases(cr, uid, action_method, phase_method, context=context)
        if phases:
            return phases[0]

        deferred_action = self._find_deferred_action(cr, uid, action_method, context=context)
        phase_pool = self.pool.get('deferred.action.phase')
        if not deferred_action:
            return phase_pool.browse(cr, uid, [], context=context)

        phase_id =\
            phase_pool.create(cr, SUPERUSER_ID, dict([('deferred_action_id', deferred_action.id), ('proc_type', 'method'), ('proc_method', phase_method)] +\
                                                     [(k, locals()[k]) for k in ['description', 'sequence', 'usage', 'execution', 'step_size']
                                                      if locals().get(k, None) is not None]),
                              context=context)
        if phase_id:
            return phase_pool.browse(cr, uid, phase_id, context=context)
        else:
            return phase_pool.browse(cr, uid, [], context=context)

    def _update_phase(self, cr, uid, vals, context=None):
        pass

    def _create_phases(self, cr, uid, action_method, context=None):
        # introspect self for methods decorated as phases for this
        # action and create new deferred.action.phase objects for each
        # found method
        for name, method in inspect.getmembers(self, predicate=inspect.ismethod):
            if getattr(method, 'phase', False) is None and method.action_method == action_method:
                method.phase = self._create_phase(cr, uid, **dict([('phase_method', name), ('context', context)] +\
                                                                  [(k, v) for k, v in method.__dict__.items()
                                                                   if k in ['action_method', 'description', 'sequence', 'usage', 'execution', 'step_size']]))

    def _find_deferred_action_for_phase(self, cr, uid, phase_method, context=None):
        action_pool = self.pool.get('deferred.action')
        phase_pool = self.pool.get('deferred.action.phase')

        action_ids = action_pool.search(cr, uid, [('model','=',self._get_model_id(cr, uid, context=context))], context=context)
        phase_ids = phase_pool.search(cr, uid, [('deferred_action_id','in',action_ids),
                                                ('proc_type','=','method'),
                                                ('proc_method','=',phase_method)],
                                      context=context)
        if phase_ids:
            phase = phase_pool.browse(cr, uid, phase_ids[0], context=context)
            return phase.deferred_action_id
        else:
            return action_pool.browse(cr, uid, [], context=context)


deferred_action_osv()
