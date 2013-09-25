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
import pooler
import logging
import datetime
from tools.safe_eval import safe_eval

_logger = logging.getLogger(__name__)

def defer_action(func):
    def new_action(self, cr, uid, ids, *args, **kwargs):
        if 'base_deferred_actions_do_not_defer' in kwargs:
            del kwargs['base_deferred_actions_do_not_defer']
            return func(self, cr, uid, ids, *args, **kwargs)
        else:
            return self.pool.get('deferred.action').create_defered_action(cr, uid, self._name, func.func_name, ids, *args, **kwargs)
    return new_action

class deferred_action(osv.osv):

    _name = 'deferred.action'

    _columns = {
        'name': fields.char('Name', size=32, required=True, readonly=True,),
        'function': fields.char('Function', size=128, required=True, readonly=True,),
        'model': fields.char('Model', size=128, required=True, readonly=True,),
        'res_id': fields.integer('Resource ID', requested=True, readonly=True,),
        'user_id': fields.many2one('res.users', required=True, string='User', readonly=True,),
        'date_requested': fields.datetime('Request Date', required=True, readonly=True,),
        'date_completed': fields.datetime('Completed Date', readonly=True,),
        'state': fields.selection([('pending', 'Pending'), ('done', 'Done'), ('fail', 'Failed'), ('cancel', 'Cancelled'),], string='State', required=True, readonly=True,),
        'args': fields.text('Arguments', readonly=True,),
        'kwargs': fields.text('Keyword Arguments', readonly=True,),
        'result': fields.text('Result', readonly=True,),
        'retry_of': fields.many2one('deferred.action', string="Retry Of", readonly=True,),
        'retrys': fields.one2many('deferred.action', 'retry_of', string="Retry Actions", readonly=True,),
    }

    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'Name must be unique !'),
    ]

    _order = 'date_requested desc'

    _defaults = {
        'name': lambda obj, cr, uid, context: obj.pool.get('ir.sequence').get(cr, uid, 'deferred.action'),
        'state': lambda *a: 'pending',
        'date_requested': lambda *a: datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
    }


    def _message(self, cr, uid, ids, title='Action started in background', message='Action started in background. You will be notified by email on completion.', context=None):
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

    def create(self, cr, uid, vals, context=None):
        action_ids = self.search(cr, uid, [('function', '=', vals.get('function')),
                                            ('model', '=', vals.get('model')),
                                            ('res_id', '=', vals.get('res_id')),
                                            ('state', '=', 'pending'),
                                            ])
        if action_ids:
            action = self.browse(cr, uid, action_ids[0])
            raise osv.except_osv('Error!', "This action has already been requested by %s at %s." % (action.user_id.name, action.date_requested))

        return super(deferred_action, self).create(cr, uid, vals, context=None)

    def copy_data(self, cr, uid, ids, default=None, context=None):
        if not default:
            default = {}
        default['state'] = 'pending'
        default['name'] = self.pool.get('ir.sequence').get(cr, uid, 'deferred.action')
        default['date_requested'] = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        default['date_completed'] = False
        default['result'] = False
        default['retrys'] = []
        default['user_id'] = uid
        return super(deferred_action, self).copy_data(cr, uid, ids, default=default, context=context)

    def create_defered_action(self, cr, uid, model, function, res_ids, *args, **kwargs):
        # Check the args and kwargs are all expressable as strings
        try:
            str_args = args.__repr__()
            str_kwargs = kwargs.__repr__()
            test_args = safe_eval(str_args)
            test_kwargs = safe_eval(str_kwargs)
        except SyntaxError(e):
            raise osv.except_osv('Error!', "Deferred action has been passed an invalid argument and cannot be completed.")
        if test_args != args or test_kwargs != kwargs:
            raise osv.except_osv('Error!', "Deferred action has been passed an invalid argument and cannot be completed.")

        new_action_ids = []

        # Log the requested actions
        for res_id in res_ids:
            new_action_id = self.create(cr, uid, {'function': function,
                                                  'model': model,
                                                  'res_id': res_id,
                                                  'user_id': uid,
                                                  'args': str_args,
                                                  'kwargs': str_kwargs})
            new_action_ids.append(new_action_id)
        self._notification_begin(cr, uid, new_action_ids, context=context)
        return self._message(cr, uid, new_action_ids, message='The action "%s.%s" has been started in the background, you will be emailed on completion of this action.' % (model, function))

    def run_scheduler(self, cr, uid, context=None):
        ids = self.search(cr, uid, [('state', '=', 'pending')], context=context)
        return self.run(cr, uid, ids, context=context)

    def run(self, cr, uid, ids, context=None):
        for action in self.browse(cr, uid, ids, context=context):
            if action.state != 'pending':
                raise osv.except_osv('Error!', "This deferred action is not pending so will not be run")
            _cr = pooler.get_db(cr.dbname).cursor()
            # Get an exclusive lock on the job
            try:
                _cr.execute("SELECT * FROM deferred_action WHERE id = %s FOR UPDATE NOWAIT" % (action.id,))
            except psycopg2.OperationalError, e:
                _cr.rollback()
                _cr.close()
                if e.pgcode == '55P03':
                    _logger.warning('Deferred Action %s is already running, skipping.' % (action.id, ))
                    continue
                else:
                    raise
            # Run the job
            try:
                args = safe_eval(action.args)
                kwargs = safe_eval(action.kwargs)
                kwargs['base_deferred_actions_do_not_defer'] = True
                res = getattr(self.pool.get(action.model), action.function)(_cr, action.user_id.id, [action.res_id,], *args, **kwargs)
                self.write(_cr, uid, action.id, {'state': 'done',
                                                'date_completed': datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
                                                'result': res,}, context=context)
                self._notification_done(_cr, uid, action.id, context=context)
                _cr.commit()
            except Exception, e:
                _cr.rollback()
                raise
                self.write(_cr, uid, action.id, {'state': 'fail',
                                                'date_completed': datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
                                                'result': e,}, context=context)
                self._notification_fail(_cr, uid, action.id, context=context)
                _cr.commit()
            finally:
                _cr.close()
        return True

    def cancel(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'cancel',
                                  'date_completed': datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
                                  'result': 'Cancelled by user %s' % (uid,)}, context=context)
        self._notification_done(cr, uid, ids, context=context)
        return True

    def retry(self, cr, uid, ids, context=None):
        retry_ids = []
        for action in self.browse(cr, uid, ids, context=context):
            if action.retrys:
                raise osv.except_osv('Error!', "This action already has a retry attempt.")
            retry_id = self.copy(cr, uid, action.id, {'retry_of': action.id}, context=context)
            retry_ids.append(retry_id)
        if not retry_ids:
            return True
        else:
            return {'name': 'Deferred Actions',
                'view_type': 'form',
                'view_mode': 'form,tree',
                'res_model': 'deferred.action',
                'view_id': False,
                'res_id': retry_ids[0],
                'type': 'ir.actions.act_window'}

    def _notification_begin(self, cr, uid, ids, context=None):
        return True

    def _notification_done(self, cr, uid, ids, context=None):
        return True

    def _notification_fail(self, cr, uid, ids, context=None):
        return True

deferred_action()
