# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2011 credativ Ltd (<http://credativ.co.uk>).
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

from osv import osv, fields
from tools.translate import _

class sale_order(osv.osv):
    _inherit = 'sale.order'

    _columns = {
        'state': fields.selection([
            ('draft', 'Quotation'),
            ('pending', 'Pending Approval'),
            ('waiting_date', 'Waiting Schedule'),
            ('manual', 'To Invoice'),
            ('progress', 'In Progress'),
            ('shipping_except', 'Shipping Exception'),
            ('invoice_except', 'Invoice Exception'),
            ('done', 'Done'),
            ('cancel', 'Cancelled')
            ], 'Order State', readonly=True, help="Gives the state of the quotation or sales order. \nThe exception state is automatically set when a cancel operation occurs in the invoice validation (Invoice Exception) or in the picking list process (Shipping Exception). \nThe 'Waiting Schedule' state is set when the invoice is confirmed but waiting for the scheduler to run on the order date.", select=True),
    }

    def action_pending(self, cr, uid, ids, context=None):
        for o in self.browse(cr, uid, ids):
            if not o.order_line:
                raise osv.except_osv(_('Error !'),_('You cannot confirm a sale order which has no line.'))
            if not o.state == 'draft':
                raise osv.except_osv(_('Error !'),_('You cannot confirm a sale order which is not in draft.'))
            self.write(cr, uid, [o.id], {'state': 'pending'})
            message = _("The quotation '%s' is now pending approval.") % (o.name,)
            self.log(cr, uid, o.id, message)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
