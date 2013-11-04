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

class account_move(osv.osv):
    _inherit = 'account.move'

    _columns = {
            'purchase_order_id': fields.many2one('purchase.order', 'Purchase Order ID', readonly=True, help='This account move indicates a payment for a non-validated invoice for this purchase order.'),
        }

account_move()

class account_invoice(osv.osv):
    _inherit = 'account.invoice'

    _columns = {
            'purchase_order_ids': fields.many2many('purchase.order', 'purchase_invoice_rel', 'invoice_id', 'purchase_id', 'Purchase Orders', help="Purchase orders related to this invoice"),
        }

    def action_move_create(self, cr, uid, ids, context=None):
        move_obj = self.pool.get('account.move')
        line_obj = self.pool.get('account.move.line')

        res = super(account_invoice, self).action_move_create(cr, uid, ids, context)

        for invoice in self.browse(cr, uid, ids, context=context):
            po_ids = [x.id for x in invoice.purchase_order_ids]
            line_ids = []
            moves = []
            src_account_id = invoice.account_id.id
            if po_ids:
                moves = move_obj.search(cr, uid, [('purchase_order_id', 'in', po_ids)], context=context)
            if moves and invoice.move_id:
                moves.append(invoice.move_id.id)
                total = 0.0
                cr.execute('SELECT id FROM account_move_line '\
                        'WHERE move_id IN %s',
                        (tuple(moves),))
                lines = line_obj.browse(cr, uid, map(lambda x: x[0], cr.fetchall()) )

                for l in lines + invoice.payment_ids:
                    if l.account_id.id == src_account_id:
                        line_ids.append(l.id)
                        total += (l.debit or 0.0) - (l.credit or 0.0)

                inv_id, name = self.name_get(cr, uid, [invoice.id], context=context)[0]
                if (not round(total,self.pool.get('decimal.precision').precision_get(cr, uid, 'Account'))):
                    self.pool.get('account.move.line').reconcile(cr, uid, line_ids, 'manual', context=context)
                else:
                    self.pool.get('account.move.line').reconcile_partial(cr, uid, line_ids, 'manual', context=context)

                self.pool.get('account.invoice').write(cr, uid, ids, {}, context=context)

        return res

account_invoice()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
