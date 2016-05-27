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

class stock_picking_in(orm.Model):
    _inherit = 'stock.picking.in'

    def _do_invoice(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        context = context.copy()
        wizard_obj = self.pool.get('stock.invoice.onshipping')
        for picking_id in ids:
            context.update({'active_model': 'stock.picking.in',
                            'active_ids': [picking_id],
                            'active_id': picking_id,})
            wizard_id = wizard_obj.create(cr, uid, {}, context=context)
            wizard_obj.open_invoice(cr, uid, [wizard_id], context=context)
        return True

    def _auto_invoice(self, cr, uid, ids, context=None):
        with closing(pooler.get_db(cr.dbname).cursor()) as _cr:
            for picking_id in ids:
                try:
                    self._do_invoice(_cr, uid, [picking_id], context=context)
                    _cr.commit()
                except Exception, e:
                    _cr.rollback()
                    formatted_info = "".join(traceback.format_exception(*(sys.exc_info())))
                    _logger.error("Error while auto creating invoice for incoming shipment %s.\n%s" % (picking_id, formatted_info))
