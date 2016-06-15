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

import sys
import traceback
import logging
from contextlib import closing

from openerp.osv import fields, orm
from openerp import pooler

_logger = logging.getLogger(__name__)

class purchase_order(orm.Model):
    _inherit = 'purchase.order'

    def _do_invoice(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        context = context.copy()
        wizard_obj = self.pool.get('purchase.order.line_invoice')
        for purchase in self.browse(cr, uid, ids, context=context):
            context.update({'active_ids' :  [line.id for line in purchase.order_line if line.invoiced != True]})
            wizard_id = wizard_obj.create(cr, uid, {}, context=context)
            wizard_obj.makeInvoices(cr, uid, [wizard_id], context=context)
        return True

    def _auto_invoice(self, cr, uid, ids, context=None):
        with closing(pooler.get_db(cr.dbname).cursor()) as _cr:
            for purchase_id in ids:
                try:
                    self._do_invoice(_cr, uid, [purchase_id], context=context)
                    _cr.commit()
                except Exception, e:
                    _cr.rollback()
                    formatted_info = "".join(traceback.format_exception(*(sys.exc_info())))
                    _logger.error("Error while auto creating invoice for purchase order %s.\n%s" % (purchase_id, formatted_info))

    def run_automatic_invoice(self, cr, uid, context=None):
        stock_picking_in_obj = self.pool.get('stock.picking.in')

        ## The field 'invoiced' is not searchable so using SQL instead
        # purchase_ids = self.search(cr, uid, [('partner_id.purchase_auto_invoice', '=', True),
        #                                      ('invoice_method', 'in', ('manual', 'order')),
        #                                      ('invoiced', '=', False)], context=context)

        cr.execute("""SELECT po.id
            FROM purchase_order po
            INNER JOIN res_partner rp
                ON rp.id = po.partner_id
            INNER JOIN purchase_order_line pol
                ON pol.order_id = po.id
            LEFT OUTER JOIN purchase_invoice_rel pil
                ON pil.purchase_id = po.id
            LEFT OUTER JOIN account_invoice ai
                ON pil.invoice_id = ai.id
                AND ai.state != 'cancel'
            WHERE po.invoice_method IN ('manual', 'order')
            AND po.state = 'approved'
            AND rp.purchase_auto_invoice = True
            AND ai.id IS NULL
            GROUP BY po.id
                HAVING bool_or(pol.invoiced = False);""")

        purchase_ids = self.search(cr, uid, [('id', 'in', [x[0] for x in cr.fetchall()])], context=context)

        self._auto_invoice(cr, uid, purchase_ids, context=context)

        picking_ids = stock_picking_in_obj.search(cr, uid, [('purchase_id', '!=', False),
                                            ('purchase_id.partner_id.purchase_auto_invoice', '=', True),
                                            ('invoice_state', '=', '2binvoiced'),
                                            ('state', '=', 'done')], context=context)
        stock_picking_in_obj._auto_invoice(cr, uid, picking_ids, context=context)

        return True
