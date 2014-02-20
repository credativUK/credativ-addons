# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2013 credativ Ltd (<http://credativ.co.uk>).
#    All Rights Reserved
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

import netsvc
from osv import osv, fields
from tools.translate import _
import tools

class purchase_order(osv.osv):
    _inherit = 'purchase.order'

    def _has_valid_invoices(self, cr, uid, ids, name, args, context=None):
        res = {}
        for id in ids:
            res[id] = False
            query = "select id from account_invoice where id in (select invoice_id from purchase_invoice_rel where purchase_id = %s) and state = 'open'"%(id)
            cr.execute(query)
            invoice_ids = tools.flatten(cr.fetchall())
            if invoice_ids:
                res[id] = True
        return res

    _columns = {
            'has_valid_invoices': fields.function(_has_valid_invoices, type='boolean', string='Has Valid Invoices'),
        }

    def check_for_invoices(self,cr,uid,ids,context=None):
        ''' Check for open invoices attached to purchase order'''

        invoice_ids = []
        if ids:
            query = "select id from account_invoice where id in (select invoice_id from purchase_invoice_rel where purchase_id = %s) and state = 'open'"%(ids[0])
            cr.execute(query)
            invoice_ids = tools.flatten(cr.fetchall())

        if not invoice_ids:
            wiz_name = _("PO Advance Payment")
        else:
            wiz_name = _("PO Payment")

        wiz_context = dict(context, active_ids=ids, active_id=ids[0])

        return {
            'name':wiz_name,
            'view_mode': 'form',
            'view_type': 'form',
            'view_id': False,
            'res_model': 'purchase.advance.payment',
            'res_id':False,
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
            'domain': '[]',
            'context': wiz_context
        }

purchase_order()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
