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

from pickle import loads, dumps, UnpicklingError

from openerp.osv import fields, orm
from openerp import SUPERUSER_ID

from openerp.addons.connector.queue.job import OpenERPJobStorage
from openerp.addons.connector.session import ConnectorSession
from openerp.addons.connector.queue.job import job

# TODO: Wrapper which creates queue_task and shows wizard to user
# TODO: Prevent duplicates being created for the same IDs with states other than done or failed
# TODO: Set security so only superuser can create a job, anybody can read
# TODO: take job sig from wrapper function only, do not allow a user to spoof their uid

# TODO: How will we raise a completion message to the user? Extend queue.job function???

def defer(name):
    def defer_wrapper(func):
        def run(cls, cr, uid, *args, **kwargs):
            """Run the origional function."""
            return func(cls, cr, uid, *args, **kwargs)

        def defer_inner(cls, cr, uid, *args, **kwargs):
            task_obj = cls.pool.get('queue.task')
            task_data = {
                    'name': name,
                    'model': cls._name,
                    'res_id': args[0][0], # FIXME: This should be optional, and also check if we are a list or integer
                    'function_name': func.__name__,
                    'func_args': dumps([args, kwargs]), # FIXME: We should handle serialisation errors here
                    'user_id': uid,
                }
            task_id = task_obj.create(cr, SUPERUSER_ID, task_data)

            return {
                    'name': 'Run a task',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'queue.task',
                    'view_id': False,
                    'res_id': task_id,
                    'type': 'ir.actions.act_window',
                    'target': 'new',
                }

        defer_inner.run = run
        return defer_inner
    return defer_wrapper

@job
def _run_task_proxy(session, model_name, record_id):
    queue_task_obj = session.pool.get('queue.task')
    return queue_task_obj.run_task(session.cr, session.uid, [record_id])

class queue_task(orm.Model):
    _name = 'queue.task'
    _description = 'Queue Task Wizard'

    def _get_duplicate(self, cr, uid, ids, prop, arg, context=None):
        res = {}
        for task in self.browse(cr, uid, ids, context=context):
            duplicate_ids = self.search(cr, uid, [('model', '=', task.model),
                                                  ('res_id', '=', task.res_id),
                                                  ('queue_job_id', '!=', False),
                                                  ('queue_job_id.state', 'not in', ('done', 'failed')),
                                                  ('id', '!=', task.id)], context=context)
            res[task.id] = duplicate_ids and True or False
        return res

    _columns = {
            'name' : fields.char('Name', size=128, required=True, readonly=True),
            'queue_job_id' : fields.many2one('queue.job', 'Queue Job', readonly=True),
            'model': fields.char('Model Name', select=1, required=True, size=64, readonly=True),
            'res_id': fields.integer('Record ID', select=1),
            'function_name': fields.char('Function Name', select=1, required=True, size=128, readonly=True),
            'func_args': fields.binary('Pickled Function Arguments', readonly=True, required=True),
            'user_id': fields.many2one('res.users', string='User ID', required=True, readonly=True),
            'duplicate': fields.function(_get_duplicate, type='boolean', string='Duplicate Job', readonly=True),
    }

    _default = {
        'state': 'draft',
    }

    def run_task(self, cr, uid, ids, context=None):
        for task in self.browse(cr, uid, ids, context=context):
            if uid !=  SUPERUSER_ID or task.user_id.id != uid: # Check we are the superuser or the current user to prevent privilege escalation
                raise orm.except_orm('Incorrect User', 'A queue task should run as either the same user or the super user')
            task_uid = task.user_id.id

            try:
                func_args = loads(task.func_args)
                (args, kwargs) = func_args
            except Exception, e:
                raise orm.except_orm('Incorrect Arguments', 'Could not parse arguments for the function')

            model = self.pool.get(task.model)
            if not model:
                raise orm.except_orm('Incorrect Model', 'Could not find model %s' % (task.model,))

            func = getattr(model, task.function_name)
            if not func:
                raise orm.except_orm('Incorrect Function', 'Could not find function %s for model %s' % (task.function_name, task.model,))
            func_call = getattr(func, 'run')
            if not func_call:
                raise orm.except_orm('Incorrect Function', 'Function %s for model %s is not configured to defer' % (task.function_name, task.model,))

            func_call(cr, task_uid, *args, **kwargs)

        return True

    def queue_task(self, cr, uid, ids, context=None):
        job_obj = self.pool.get('queue.job')
        session = ConnectorSession(cr, uid, context=context)
        for id in ids:
            job_uuid = _run_task_proxy.delay(session, 'queue.job', id)
            job_ids = job_obj.search(cr, SUPERUSER_ID, [('uuid', '=', job_uuid)], context=context, limit=1)
            if not job_ids:
                raise orm.except_orm('Could not queue job', 'Job could not be queued in the background')

            self.write(cr, uid, [id], {'queue_job_id': job_ids[0]}, context=context)
        return True # TODO: Return a message to say job has been queued in the background


class res_partner(orm.Model):
    _inherit = 'res.partner'

    @defer('Res Partner Test')
    def test(self, cr, uid, ids, context=None):
        print "It works!"
        return 6