# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    This module copyright (C) 2013 Therp BV (<http://therp.nl>).
#    Contributors: credativ ltd (<http://www.credativ.co.uk>).
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

from openerp.osv import orm, fields


class payment_order(orm.Model):
    _inherit = "payment.order"
    _columns = {
        'aggregate': fields.related('mode', 'aggregate', type='boolean',
                                     string='Aggregate', readonly=True,
            help='Tick this box to aggregate payment lines on partners'),
        }

    def action_sent(self, cr, uid, ids, context=None):
        """
            Write order state to sent after chained wizard is successfully run.
        """
        vals = super(payment_order, self).action_sent(cr, uid, ids,
                                                               context=context)
        self.write(cr, uid, ids, {'state':'sent'}, context=context)
        return vals

class payment_line(orm.Model):
    _inherit = 'payment.line'
    _columns = {
        'move_ids': fields.many2many(
                            'account.move.line',
                            'payment_order_move_line_rel',
                            'line_id',
                            'order_line_id',
                             string="Aggregate Moves Lines",
                             readonly=True,
                                    ),
        }
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

