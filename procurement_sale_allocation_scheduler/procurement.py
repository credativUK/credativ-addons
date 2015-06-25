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

    def _procure_confirm(self, cr, uid, ids=None, use_new_cursor=False, context=None):
        procurement_obj = self.pool.get('procurement.order')
        purchase_obj = self.pool.get('purchase.order')
        purchase_line_obj = self.pool.get('purchase.order.line')
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
        # Standard Allocate
        res = super(ProcurementOrder, self)._procure_confirm(cr, uid, ids=ids, use_new_cursor=use_new_cursor, context=context)
        # Allocate MTS to MTO if no stock
        try:
            offset = 0
            if use_new_cursor:
                cr = pooler.get_db(use_new_cursor).cursor()
            while True:
                report_ids = []
                ids = procurement_obj.search(cr, uid, [('state', 'in', ('confirmed', 'exception')), ('procure_method', '=', 'make_to_stock')], offset=offset, limit=200, order='priority, date_planned', context=context)
                for proc in procurement_obj.browse(cr, uid, ids):
                    if maxdate >= proc.date_planned:
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
        # Allocate running MTO to MTS if stock available
        try:
            offset = 0
            if use_new_cursor:
                cr = pooler.get_db(use_new_cursor).cursor()
            while True:
                report_ids = []
                ids = procurement_obj.search(cr, uid, [('state', '=', 'running'), ('purchase_id', '!=', False), ('procure_method', '=', 'make_to_order')], offset=offset, limit=200, order='priority, date_planned', context=context)
                for proc in procurement_obj.browse(cr, uid, ids):
                    if maxdate >= proc.date_planned:
                        cr.execute('SAVEPOINT mto_to_stock')
                        try:
                            procurement_obj.write(cr, uid, [proc.id], {'purchase_id': False,}, context=context)
                            wf_service.trg_validate(uid, 'procurement.order', proc.id, 'button_check', cr)
                            proc.refresh()
                            # Moved to exception since no MTS stock is available, rollback and try the next one
                            if proc.state == 'exception':
                                cr.execute('ROLLBACK TO SAVEPOINT mto_to_stock')
                        except Exception, e: # A variety of errors may prevent this from re-assigning, picking exported to WMS, PO cut-off, etc
                            cr.execute('ROLLBACK TO SAVEPOINT mto_to_stock')
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
