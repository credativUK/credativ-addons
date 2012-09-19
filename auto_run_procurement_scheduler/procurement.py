# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2011 credativ ltd (<http://www.credativ.co.uk>). All Rights Reserved
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

import logging
import threading

import psycopg2

from osv import fields, osv
import pooler


def id_get(cr, uid, pool, id_str):
    mod, id_str = id_str.split('.')
    ir_model_data = pool.get('ir.model.data')
    result = ir_model_data._get_id(cr, uid, mod, id_str)
    return int(ir_model_data.read(cr, uid, [result], ['res_id'])[0]['res_id'])


class procurement_order(osv.osv):
    _inherit = "procurement.order"

    def run_scheduler(self, cr, uid, automatic=False, use_new_cursor=False, context=None):
        logger = logging.getLogger('procurement.order')
        logger.info('Starting procurement scheduler.')
        task_cr = pooler.get_db(cr.dbname).cursor()
        # TODO: what if this scheduler has been deleted?
        cron_id = id_get(task_cr, uid, self.pool, 'procurement.ir_cron_scheduler_action')
        try:
            # Try to grab an exclusive lock on the job row from within the task transaction
            task_cr.execute("""SELECT *
                               FROM ir_cron
                               WHERE id=%s
                               FOR UPDATE NOWAIT""",
                            (cron_id, ), log_exceptions=False)
            return super(procurement_order, self).run_scheduler(cr, uid, automatic=automatic,
                                                                use_new_cursor=use_new_cursor, context=context)
        except psycopg2.OperationalError, e:
            if e.pgcode == '55P03':
                # Class 55: Object not in prerequisite state; 55P03: lock_not_available
                logger.warn('Another process/thread is already busy executing the procurement scheduler, skipping it.')
            else:
                raise
        finally:
            task_cr.close()
            logger.info('Procurement scheduler finished.')


procurement_order()


class RunAgainLock(object):
    """
    A lock similar to the simple threading.Lock but records if someone tried
    to get the lock and failed.  This is useful to know if you should re-run
    an action.
    """
    def __init__(self):
        self.acquire_lock = threading.Lock()
        self.lock = threading.Lock()
        self._run_again = False
    
    def acquire(self):
        self.acquire_lock.acquire()
        try:
            if not self.lock.acquire(False):
                self._run_again = True
                return False
            return True
        finally:
            self.acquire_lock.release()

    def release(self):
        self.lock.release()

    def run_again(self):
        self.acquire_lock.acquire()
        try:
            run_again = self._run_again
            self._run_again = False
            return run_again
        finally:
            self.acquire_lock.release()


class procurement_compute_all(osv.osv_memory):
    _inherit = 'procurement.order.compute.all'

    lock = RunAgainLock()

    def _procure_calculation_all(self, cr, uid, ids, context=None):
        logger = logging.getLogger('procurement.order')

        if self.lock.acquire():
            while True:
                res = super(procurement_compute_all, self)._procure_calculation_all(cr, uid, ids, context=context)
                logger.info('The scheduler is trying to get a lock')
                if not self.lock.run_again():
                    break
            self.lock.release()
            logger.info('The scheduler has released the lock')
        else:
            logger.warn('The scheduler could not get a lock')
            res = {}
        return res


procurement_compute_all()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: