# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 credativ ltd (<http://www.credativ.co.uk>). All Rights Reserved
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

from datetime import datetime
from dateutil.relativedelta import relativedelta
from psycopg2 import OperationalError
import traceback

from openerp import netsvc
from openerp import pooler
from openerp.osv import osv
from openerp.osv import fields
from openerp.tools.translate import _
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
from openerp import tools

import logging
_logger = logging.getLogger(__name__)

PROC_ERROR = 'Error running procurement scheduler'

class AttemptProcurement(object):
    def __init__(self, cr, proc):
        self.cr = cr
        self.proc = proc

    def __enter__(self):
        self.cr.execute("SAVEPOINT attempt_procurement")
        return self.cr

    def __exit__(self, ex_type, ex_value, tb):
        if ex_type and ex_type != OperationalError: # We have an exception, mark the procurement as such
            self.cr.execute("ROLLBACK TO SAVEPOINT attempt_procurement")
            if self.proc.message != PROC_ERROR:
                self.proc.message_post(body='%s:<br/>\n<br/>\n<pre>%s</pre>' % (PROC_ERROR, traceback.format_exc()))
                self.proc.write({'message': PROC_ERROR})
        elif ex_type and ex_type == OperationalError: # We have an exception, but it is just an opperational error, ignore it
            self.cr.execute("ROLLBACK TO SAVEPOINT attempt_procurement")

        self.cr.execute("RELEASE SAVEPOINT attempt_procurement")
        return True # Danger, this supresses any exceptions, this is what we want

class ProcurementOrder(osv.Model):
    _inherit = 'procurement.order'

    def _procure_confirm_mto_confirmed_to_mts(self, cr, uid, ids=None, use_new_cursor=False, context=None):
        if context is None:
            context = {}
        procurement_obj = self.pool.get('procurement.order')
        location_obj = self.pool.get('stock.location')
        wf_service = netsvc.LocalService("workflow")
        company = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id
        maxdate = (datetime.today() + relativedelta(days=company.schedule_range)).strftime(tools.DEFAULT_SERVER_DATE_FORMAT)
        max_sched_condition = context.get('_sched_max_proc_id') and ('id', '<=', context.get('_sched_max_proc_id')) or ('id', '!=', 0)

        # Allocate confirmed MTO to MTS if stock available
        try:
            if use_new_cursor:
                cr = pooler.get_db(use_new_cursor).cursor()
            ids = []
            prev_ids = []
            while True:
                ids = procurement_obj.search(cr, uid, [('date_planned', '<', maxdate), max_sched_condition, ('note', 'not like', '%_mto_to_mts_done_%'), '|',
                                                           '&', ('state', '=', 'confirmed'), ('procure_method', '=', 'make_to_order'),
                                                           '&', '&', ('state', 'in', ('confirmed', 'exception')), ('procure_method', '=', 'make_to_stock'), ('note', 'like', '%_mto_to_mts_fail_%')], limit=50, order='priority, date_planned', context=context)
                _logger.info('Processing procurements %s' % ids)
                for proc in procurement_obj.browse(cr, uid, ids):
                    with AttemptProcurement(cr, proc):
                        ok = True
                        if proc.move_id:
                            # Check if there is qty at this location but do not yet reserve it.
                            # Reservation can fail due to transient errors, we want to keep retrying these
                            ok = location_obj._product_reserve(cr, uid, [proc.move_id.location_id.id], proc.move_id.product_id.id, proc.move_id.product_qty, {'uom': proc.move_id.product_uom.id}, lock=False)
                        if ok:
                            if proc.state == 'exception':
                                wf_service.trg_validate(uid, 'procurement.order', proc.id, 'button_restart', cr)
                            if proc.procure_method != 'make_to_stock':
                                procurement_obj.write(cr, uid, [proc.id], {'procure_method': 'make_to_stock'}, context=context)
                            wf_service.trg_validate(uid, 'procurement.order', proc.id, 'button_check', cr)
                            proc.refresh()
                            # Moved to exception since another thread might be reserving it instead, rollback and try again later
                            if proc.state == 'exception' and '_mto_to_mts_fail_' not in proc.note:
                                _logger.info('Procurement %s entered exception state.' % proc.id)
                                cr.execute("""UPDATE procurement_order set note = TRIM(both E'\n' FROM COALESCE(note, '') || %s) WHERE id = %s""", ('\n\n_mto_to_mts_fail_',proc.id))
                        else:
                            # No stock is available, continue
                            cr.execute("""UPDATE procurement_order set note = TRIM(both E'\n' FROM COALESCE(note, '') || %s) WHERE id = %s""", ('\n\n_mto_to_mts_done_',proc.id))
                            if proc.state == 'exception':
                                wf_service.trg_validate(uid, 'procurement.order', proc.id, 'button_restart', cr)
                            if proc.procure_method != 'make_to_order':
                                procurement_obj.write(cr, uid, [proc.id], {'procure_method': 'make_to_order'}, context=context)
                if use_new_cursor:
                    cr.commit()
                if not ids or prev_ids == ids:
                    break
                else:
                    prev_ids = ids
        finally:
            if use_new_cursor:
                try:
                    cr.close()
                except Exception:
                    pass
        return True

    def _procure_confirm_mts_exception_to_mto(self, cr, uid, ids=None, use_new_cursor=False, context=None):
        if context is None:
            context = {}
        procurement_obj = self.pool.get('procurement.order')
        purchase_obj = self.pool.get('purchase.order')
        purchase_line_obj = self.pool.get('purchase.order.line')
        wf_service = netsvc.LocalService("workflow")
        company = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id
        maxdate = (datetime.today() + relativedelta(days=company.schedule_range)).strftime(tools.DEFAULT_SERVER_DATE_FORMAT)
        max_sched_condition = context.get('_sched_max_proc_id') and ('id', '<=', context.get('_sched_max_proc_id')) or ('id', '!=', 0)
        try:
            if use_new_cursor:
                cr = pooler.get_db(use_new_cursor).cursor()
            exclude_prod_loc = [] # List of (product_id, location_id) for indicating no stock is available
            ids = []
            prev_ids = []
            while True:
                ids = procurement_obj.search(cr, uid, [('date_planned', '<', maxdate), max_sched_condition, ('state', 'in', ('confirmed', 'exception')), ('procure_method', '=', 'make_to_stock')], limit=50, order='priority, date_planned', context=context)
                for proc in procurement_obj.browse(cr, uid, ids):
                    with AttemptProcurement(cr, proc):
                        # We already know there are no POs available, skip
                        if (proc.product_id.id, proc.location_id.id) in exclude_prod_loc:
                            continue
                        # Find purchase lines for this product
                        po_ids = []
                        pol_ids = purchase_line_obj.search(cr, uid, [
                                    ('state', '=', 'confirmed'),
                                    ('product_id', '=', proc.product_id.id),
                                    ('move_dest_id', '=', False),
                                    ('order_id.location_id', '=', proc.location_id.id),
                                    ('order_id.procurements_auto_allocate', '=', True),
                                ], order='date_planned asc', context=context)
                        if pol_ids:
                            for pol in purchase_line_obj.read(cr, uid, pol_ids, ['order_id'], context=context):
                                if pol['order_id'][0] not in po_ids:
                                    po_ids.append(pol['order_id'][0])
                        if not po_ids:
                            exclude_prod_loc.append((proc.product_id.id, proc.location_id.id))
                        for po_id in po_ids:
                            context.update({'psa_skip_moves': True})
                            if purchase_obj.allocate_check_stock(cr, uid, [po_id], [proc.id], context=context) and \
                                    not purchase_obj.allocate_check_restrict(cr, uid, [po_id], context=context):
                                if proc.state == 'exception':
                                    wf_service.trg_validate(uid, 'procurement.order', proc.id, 'button_restart', cr)
                                wf_service.trg_validate(uid, 'procurement.order', proc.id, 'button_check', cr)
                                procurement_obj.write(cr, uid, [proc.id], {'purchase_id': po_id}, context=context)
                                break
                if use_new_cursor:
                    cr.commit()
                if not ids or prev_ids == ids:
                    break
                else:
                    prev_ids = ids
                if not ids: break
        finally:
            if use_new_cursor:
                try:
                    cr.close()
                except Exception:
                    pass
        return True

    def _procure_confirm_mto_running_to_mts(self, cr, uid, ids=None, use_new_cursor=False, context=None):
        if context is None:
            context = {}
        procurement_obj = self.pool.get('procurement.order')
        product_obj = self.pool.get('product.product')
        wf_service = netsvc.LocalService("workflow")
        company = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id
        maxdate = (datetime.today() + relativedelta(days=company.schedule_range)).strftime(tools.DEFAULT_SERVER_DATE_FORMAT)
        current_datetime = (datetime.today() - relativedelta(seconds=2*60*60)).strftime(tools.DEFAULT_SERVER_DATETIME_FORMAT)
        max_sched_condition = context.get('_sched_max_proc_id') and ('id', '<=', context.get('_sched_max_proc_id')) or ('id', '!=', 0)
        try:
            if use_new_cursor:
                cr = pooler.get_db(use_new_cursor).cursor()
            # Get list of products to be checked
            cr.execute("""SELECT pp.id
                            FROM procurement_order proc
                        INNER JOIN product_product pp ON pp.id = proc.product_id
                        WHERE proc.state = 'running'
                            AND proc.purchase_id IS NOT NULL
                            AND proc.procure_method = 'make_to_order'
                            AND proc.date_planned <= %s
                            AND proc.product_id IN
                                (SELECT DISTINCT pp.id FROM product_product pp
                                INNER JOIN stock_move sm
                                ON sm.product_id = pp.id
                                AND (pp.date_mto_mts_allocate IS NULL
                                OR COALESCE(sm.write_date, sm.create_date) > pp.date_mto_mts_allocate))
                        GROUP BY pp.id ORDER BY pp.date_mto_mts_allocate""", (maxdate,))
            product_ids = [x[0] for x in cr.fetchall()]
            for product_id in product_ids:
                stock_prod_loc = {} # Dict of {location_id: qty} for last stock failure qty, anything >= should skip
                ids = []
                prev_ids = []
                while True:
                    ids = procurement_obj.search(cr, uid, [max_sched_condition, ('product_id', '=', product_id), ('state', '=', 'running'), ('purchase_id', '!=', False),
                                                           ('procure_method', '=', 'make_to_order'), ('date_planned', '<=', maxdate)], limit=50, order='priority, date_planned', context=context)
                    for proc in procurement_obj.browse(cr, uid, ids):
                        _logger.info("_procure_confirm_mto_running_to_mts: Product %s procurement %s - begin" % (proc.product_id.id, proc.id))
                        max_qty = stock_prod_loc.get(proc.location_id.id)
                        if max_qty is not None and proc.product_qty >= max_qty:
                            _logger.info("_procure_confirm_mto_running_to_mts: Product %s procurement %s - skipping due to max qty %s >= %s" % (proc.product_id.id, proc.id, proc.product_qty, max_qty))
                            continue
                        cr.execute('SAVEPOINT mto_to_stock')
                        try:
                            procurement_obj.write(cr, uid, [proc.id], {'purchase_id': False,}, context=context)
                            proc.refresh()
                            if proc.state == 'exception':
                                wf_service.trg_validate(uid, 'procurement.order', proc.id, 'button_restart', cr)
                                proc.refresh()
                            wf_service.trg_validate(uid, 'procurement.order', proc.id, 'button_check', cr)
                            proc.refresh()
                            # Moved to exception since no MTS stock is available, rollback and try the next one
                            if proc.state == 'exception':
                                cr.execute('ROLLBACK TO SAVEPOINT mto_to_stock')
                                stock_prod_loc[proc.location_id.id] = proc.product_qty
                                _logger.info("_procure_confirm_mto_running_to_mts: Product %s procurement %s - checked, state = %s, message = %s" % (proc.product_id.id, proc.id, proc.state, proc.message))
                            else:
                                _logger.info("_procure_confirm_mto_running_to_mts: Product %s procurement %s - successful" % (proc.product_id.id, proc.id))
                        except Exception, e: # A variety of errors may prevent this from re-assigning, picking exported to WMS, PO cut-off, etc
                            _logger.info("_procure_confirm_mto_running_to_mts: Product %s procurement %s - rolling back - Exception %s" % (proc.product_id.id, proc.id, e))
                            cr.execute('ROLLBACK TO SAVEPOINT mto_to_stock')
                        cr.execute('RELEASE SAVEPOINT mto_to_stock')
                    if use_new_cursor:
                        cr.commit()
                    if not ids or prev_ids == ids:
                        product_obj.write(cr, uid, [product_id], {'date_mto_mts_allocate': current_datetime}, context=context)
                        break
                    else:
                        prev_ids = ids
        finally:
            if use_new_cursor:
                try:
                    cr.commit()
                    cr.close()
                except Exception:
                    pass
        return True

    def _orig_procure_confirm(self, cr, uid, ids=None, use_new_cursor=False, context=None):
        '''
        Call the scheduler to check the procurement order

        @param self: The object pointer
        @param cr: The current row, from the database cursor,
        @param uid: The current user ID for security checks
        @param ids: List of selected IDs
        @param use_new_cursor: False or the dbname
        @param context: A standard dictionary for contextual values
        @return:  Dictionary of values
        '''
        if context is None:
            context = {}
        max_sched_condition = context.get('_sched_max_proc_id') and ('id', '<=', context.get('_sched_max_proc_id')) or ('id', '!=', 0)
        try:
            if use_new_cursor:
                cr = pooler.get_db(use_new_cursor).cursor()
            wf_service = netsvc.LocalService("workflow")

            procurement_obj = self.pool.get('procurement.order')
            if not ids:
                ids = procurement_obj.search(cr, uid, [max_sched_condition, ('state', '=', 'exception')], order="date_planned")
            for id in ids:
                wf_service.trg_validate(uid, 'procurement.order', id, 'button_restart', cr)
            if use_new_cursor:
                cr.commit()
            company = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id
            maxdate = (datetime.today() + relativedelta(days=company.schedule_range)).strftime(tools.DEFAULT_SERVER_DATE_FORMAT)
            prev_ids = []
            while True:
                ids = procurement_obj.search(cr, uid, [max_sched_condition, ('state', '=', 'confirmed'), ('procure_method', '=', 'make_to_order'), ('date_planned', '<', maxdate)], limit=100, order='priority, date_planned', context=context)
                for proc in procurement_obj.browse(cr, uid, ids, context=context):
                    with AttemptProcurement(cr, proc):
                        wf_service.trg_validate(uid, 'procurement.order', proc.id, 'button_check', cr)
                if use_new_cursor:
                    cr.commit()
                if not ids or prev_ids == ids:
                    break
                else:
                    prev_ids = ids
            ids = []
            prev_ids = []
            while True:
                ids = procurement_obj.search(cr, uid, [max_sched_condition, ('state', '=', 'confirmed'), ('procure_method', '=', 'make_to_stock'), ('date_planned', '<', maxdate)], limit=100)
                for proc in procurement_obj.browse(cr, uid, ids):
                    with AttemptProcurement(cr, proc):
                        wf_service.trg_validate(uid, 'procurement.order', proc.id, 'button_check', cr)
                if use_new_cursor:
                    cr.commit()
                if not ids or prev_ids == ids:
                    break
                else:
                    prev_ids = ids

            if use_new_cursor:
                cr.commit()
        finally:
            if use_new_cursor:
                try:
                    cr.close()
                except Exception:
                    pass
        return {}

    def _get_procure_functions(self, cr, uid, ids=None, use_new_cursor=False, context=None):
        return [
            self._procure_confirm_mto_confirmed_to_mts, # Allocate confirmed MTO to MTS if stock available
            self._orig_procure_confirm, # Standard Allocate with some customisations
            self._procure_confirm_mts_exception_to_mto, # Allocate MTS to MTO if no stock
            self._procure_confirm_mto_running_to_mts, # Allocate running MTO to MTS if stock available
        ]

    def _procure_confirm(self, cr, uid, ids=None, use_new_cursor=False, context=None):
        if context is None:
            context = {}
        functions = self._get_procure_functions(cr, uid, ids=ids, use_new_cursor=use_new_cursor, context=context)
        cr.execute("select max(id) from procurement_order") # Take the max proc id so we ignore new procurements created after we started
        context['_sched_max_proc_id'] = cr.fetchall()[0][0]
        exceptions = []
        for func in functions:
            try:
                func(cr, uid, ids=ids, use_new_cursor=use_new_cursor, context=context)
            except OperationalError, e:
                exception = "OperationalError while %s running scheduler, continue [%s]:\n\n%s" % (e, use_new_cursor, traceback.format_exc())
                _logger.error(exception)
                exceptions.append(exception)
                if not use_new_cursor:
                    raise e

        return True

    def action_po_assign(self, cr, uid, ids, context=None):
        purchase_obj = self.pool.get('purchase.order')
        purchase_line_obj = self.pool.get('purchase.order.line')
        other_ids = []
        res = []

        for proc in self.browse(cr, uid, ids, context=context):
            if proc.procure_method == 'make_to_order' and not proc.purchase_id:
                po_ids = []
                pol_ids = purchase_line_obj.search(cr, uid, [
                            ('state', '=', 'confirmed'),
                            ('product_id', '=', proc.product_id.id),
                            ('move_dest_id', '=', False),
                            ('order_id.location_id', '=', proc.location_id.id),
                            ('order_id.procurements_auto_allocate', '=', True),
                        ], order='date_planned asc', context=context)
                if pol_ids:
                    for pol in purchase_line_obj.read(cr, uid, pol_ids, ['order_id'], context=context):
                        if pol['order_id'][0] not in po_ids:
                            po_ids.append(pol['order_id'][0])
                for po_id in po_ids:
                    if purchase_obj.allocate_check_stock(cr, uid, [po_id], [proc.id], context=context) and \
                            not purchase_obj.allocate_check_restrict(cr, uid, [po_id], context=context):
                        self.write(cr, uid, [proc.id], {'purchase_id': po_id}, context=context)
                        self._confirm_po_assign(cr, uid, [proc.id,], context=context)
                        res.append(po_id)
                        break
                else:
                    other_ids.append(proc.id)
            else:
                other_ids.append(proc.id)

        if other_ids:
            purchase_ids = super(ProcurementOrder, self).action_po_assign(cr, uid, other_ids, context=context)
            if purchase_ids:
                res.append(purchase_ids)

        return len(res) and res[0] or 0

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
