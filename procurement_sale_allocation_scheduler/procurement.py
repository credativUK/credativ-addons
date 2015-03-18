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
        res = super(ProcurementOrder, self)._procure_confirm(cr, uid, ids=ids, use_new_cursor=use_new_cursor, context=context)
        wf_service = netsvc.LocalService("workflow")
        try:
            company = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id
            maxdate = (datetime.today() + relativedelta(days=company.schedule_range)).strftime(tools.DEFAULT_SERVER_DATE_FORMAT)
            offset = 0
            if use_new_cursor:
                cr = pooler.get_db(use_new_cursor).cursor()
            while True:
                report_ids = []
                ids = procurement_obj.search(cr, uid, [('state', 'in', ('confirmed', 'exception')), ('procure_method', '=', 'make_to_stock')], offset=offset)
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
        return res
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
