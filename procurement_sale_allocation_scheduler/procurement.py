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
from openerp import netsvc
from openerp import pooler
from openerp.osv import osv
from openerp.osv import fields
from openerp.tools.translate import _
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
from openerp import tools

class ProcurementOrder(osv.Model):
    _inherit = 'procurement.order'

    def _procure_confirm_mto_confirmed_to_mts(self, cr, uid, ids=None, use_new_cursor=False, context=None):
        procurement_obj = self.pool.get('procurement.order')
        wf_service = netsvc.LocalService("workflow")
        company = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id
        maxdate = (datetime.today() + relativedelta(days=company.schedule_range)).strftime(tools.DEFAULT_SERVER_DATE_FORMAT)

        # Allocate confirmed MTO to MTS if stock available
        try:
            offset = 0
            if use_new_cursor:
                cr = pooler.get_db(use_new_cursor).cursor()
            while True:
                report_ids = []
                ids = procurement_obj.search(cr, uid, [('state', '=', 'confirmed'), ('procure_method', '=', 'make_to_order'), ('note', 'not like', '%_mto_to_mts_done_%')], offset=offset, limit=200, order='priority, date_planned', context=context)
                for proc in procurement_obj.browse(cr, uid, ids):
                    if maxdate >= proc.date_planned:
                        cr.execute('SAVEPOINT mto_to_stock')
                        procurement_obj.write(cr, uid, [proc.id], {'procure_method': 'make_to_stock'}, context=context)
                        wf_service.trg_validate(uid, 'procurement.order', proc.id, 'button_check', cr)
                        proc.refresh()
                        # Moved to exception since no MTS stock is available, rollback and try the next one
                        if proc.state == 'exception':
                            cr.execute('ROLLBACK TO SAVEPOINT mto_to_stock')
                            cr.execute("""UPDATE procurement_order set note = TRIM(both E'\n' FROM COALESCE(note, '') || %s) WHERE id = %s""", ('\n\n_mto_to_mts_done_',proc.id))
                        cr.execute('RELEASE SAVEPOINT mto_to_stock')
                if use_new_cursor:
                    cr.commit()
                offset += len(ids)
                if not ids: break
        finally:
            if use_new_cursor:
                try:
                    cr.close()
                except Exception:
                    pass
        return True

    def _procure_confirm_mts_exception_to_mto(self, cr, uid, ids=None, use_new_cursor=False, context=None):
        procurement_obj = self.pool.get('procurement.order')
        purchase_obj = self.pool.get('purchase.order')
        purchase_line_obj = self.pool.get('purchase.order.line')
        wf_service = netsvc.LocalService("workflow")
        company = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id
        maxdate = (datetime.today() + relativedelta(days=company.schedule_range)).strftime(tools.DEFAULT_SERVER_DATE_FORMAT)
        try:
            offset = 0
            if use_new_cursor:
                cr = pooler.get_db(use_new_cursor).cursor()
            exclude_prod_loc = [] # List of (product_id, location_id) for indicating no stock is available
            while True:
                report_ids = []
                ids = procurement_obj.search(cr, uid, [('state', 'in', ('confirmed', 'exception')), ('procure_method', '=', 'make_to_stock')], offset=offset, limit=200, order='priority, date_planned', context=context)
                for proc in procurement_obj.browse(cr, uid, ids):
                    if maxdate >= proc.date_planned:
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
                            if purchase_obj.allocate_check_stock(cr, uid, [po_id], [proc.id], context=context) and \
                                    not purchase_obj.allocate_check_restrict(cr, uid, [po_id], context=context):
                                if proc.state == 'exception':
                                    wf_service.trg_validate(uid, 'procurement.order', proc.id, 'button_restart', cr)
                                wf_service.trg_validate(uid, 'procurement.order', proc.id, 'button_check', cr)
                                procurement_obj.write(cr, uid, [proc.id], {'purchase_id': po_id}, context=context)
                                break
                if use_new_cursor:
                    cr.commit()
                offset += len(ids)
                if not ids: break
        finally:
            if use_new_cursor:
                try:
                    cr.close()
                except Exception:
                    pass
        return True

    def _procure_confirm_mto_running_to_mts(self, cr, uid, ids=None, use_new_cursor=False, context=None):
        procurement_obj = self.pool.get('procurement.order')
        product_obj = self.pool.get('product.product')
        wf_service = netsvc.LocalService("workflow")
        company = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id
        maxdate = (datetime.today() + relativedelta(days=company.schedule_range)).strftime(tools.DEFAULT_SERVER_DATE_FORMAT)
        current_datetime = (datetime.today() - relativedelta(seconds=2*60*60)).strftime(tools.DEFAULT_SERVER_DATETIME_FORMAT)
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
                offset = 0
                stock_prod_loc = {} # Dict of {location_id: qty} for last stock failure qty, anything >= should skip
                while True:
                    report_ids = []
                    ids = procurement_obj.search(cr, uid, [('product_id', '=', product_id), ('state', '=', 'running'), ('purchase_id', '!=', False),
                                                           ('procure_method', '=', 'make_to_order'), ('date_planned', '<=', maxdate)], offset=offset, limit=200, order='priority, date_planned', context=context)
                    for proc in procurement_obj.browse(cr, uid, ids):
                        max_qty = stock_prod_loc.get(proc.location_id.id)
                        if max_qty is not None and proc.product_qty >= max_qty:
                            continue
                        cr.execute('SAVEPOINT mto_to_stock')
                        try:
                            procurement_obj.write(cr, uid, [proc.id], {'purchase_id': False,}, context=context)
                            wf_service.trg_validate(uid, 'procurement.order', proc.id, 'button_check', cr)
                            proc.refresh()
                            # Moved to exception since no MTS stock is available, rollback and try the next one
                            if proc.state == 'exception':
                                cr.execute('ROLLBACK TO SAVEPOINT mto_to_stock')
                                stock_prod_loc[proc.location_id.id] = proc.product_qty
                        except Exception, e: # A variety of errors may prevent this from re-assigning, picking exported to WMS, PO cut-off, etc
                            cr.execute('ROLLBACK TO SAVEPOINT mto_to_stock')
                        cr.execute('RELEASE SAVEPOINT mto_to_stock')
                    if use_new_cursor:
                        cr.commit()
                    offset += len(ids)
                    if not ids:
                        product_obj.write(cr, uid, [product_id], {'date_mto_mts_allocate': current_datetime}, context=context)
                        break
        finally:
            if use_new_cursor:
                try:
                    cr.commit()
                    cr.close()
                except Exception:
                    pass
        return True


    def _procure_confirm(self, cr, uid, ids=None, use_new_cursor=False, context=None):
        # Allocate confirmed MTO to MTS if stock available
        self._procure_confirm_mto_confirmed_to_mts(cr, uid, ids=ids, use_new_cursor=use_new_cursor, context=context)
        # Standard Allocate
        res = super(ProcurementOrder, self)._procure_confirm(cr, uid, ids=ids, use_new_cursor=use_new_cursor, context=context)
        # Allocate MTS to MTO if no stock
        self._procure_confirm_mts_exception_to_mto(cr, uid, ids=ids, use_new_cursor=use_new_cursor, context=context)
        # Allocate running MTO to MTS if stock available
        self._procure_confirm_mto_running_to_mts(cr, uid, ids=ids, use_new_cursor=use_new_cursor, context=context)

        return res

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
