# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2012 credativ (http://www.credativ.co.uk). All Rights Reserved
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

from osv import fields, osv
from tools.translate import _
import netsvc
from mx import DateTime

class sale(osv.osv):
    _inherit = 'sale.order'
    
    def _prepare_order_line_move(self, cr, uid, order, line, picking_id, date_planned, qty=None, context=None):
        location_id = order.shop_id.warehouse_id.lot_stock_id.id
        output_id = order.shop_id.warehouse_id.lot_output_id.id
        return {
            'name': line.name[:250],
            'picking_id': picking_id,
            'product_id': line.product_id.id,
            'date': date_planned,
            'date_expected': date_planned,
            'product_qty': qty or line.product_uom_qty,
            'product_uom': line.product_uom.id,
            'product_uos_qty': qty or (line.product_uos and line.product_uos_qty) or line.product_uom_qty,
            'product_uos': (line.product_uos and line.product_uos.id)\
                    or line.product_uom.id,
            'product_packaging': line.product_packaging.id,
            'address_id': line.address_allotment_id.id or order.partner_shipping_id.id,
            'location_id': location_id,
            'location_dest_id': output_id,
            'sale_line_id': line.id,
            'tracking_id': False,
            'state': 'draft',
            #'state': 'waiting',
            'note': line.notes,
            'company_id': order.company_id.id,
            'price_unit': line.product_id.standard_price or 0.0
        }
    
    def _create_pickings_and_procurements(self, cr, uid, order, order_lines, picking_id=False, context=None):
        """Create the required procurements to supply sale order lines, also connecting
        the procurements to appropriate stock moves in order to bring the goods to the
        sale order's requested location.

        If ``picking_id`` is provided, the stock moves will be added to it, otherwise
        a standard outgoing picking will be created to wrap the stock moves, as returned
        by :meth:`~._prepare_order_picking`.

        Modules that wish to customize the procurements or partition the stock moves over
        multiple stock pickings may override this method and call ``super()`` with
        different subsets of ``order_lines`` and/or preset ``picking_id`` values.

        :param browse_record order: sale order to which the order lines belong
        :param list(browse_record) order_lines: sale order line records to procure
        :param int picking_id: optional ID of a stock picking to which the created stock moves
                               will be added. A new picking will be created if ommitted.
        :return: True
        """
        wf_service = netsvc.LocalService("workflow")
        move_obj = self.pool.get('stock.move')
        picking_obj = self.pool.get('stock.picking')
        procurement_obj = self.pool.get('procurement.order')
        proc_ids = []

        for line in order_lines:
            if line.state == 'done':
                continue

            picking_ids = []
            move_ids = []
            date_planned = self._get_date_planned(cr, uid, order, line, order.date_order, context=context)

            if line.product_id:
                if line.product_id.product_tmpl_id.type in ('product', 'consu'):
                    
                    if picking_id:
                        move_id = move_obj.create(cr, uid, self._prepare_order_line_move(cr, uid, order, line, picking_id, date_planned, context=context))
                    else:
                        move_id = False
                        for i in range(0, int(line.product_uom_qty)):
                            i_picking_id = picking_obj.create(cr, uid, self._prepare_order_picking(cr, uid, order, context=context))
                            picking_ids.append(i_picking_id)
                            i_move_id = move_obj.create(cr, uid, self._prepare_order_line_move(cr, uid, order, line, i_picking_id, date_planned, qty=1,  context=context))
                            move_ids.append(i_move_id)
                else:
                    # a service has no stock move
                    move_id = False

                # Will use the last stock move to link to the procurement if there are more than one
                proc_id = procurement_obj.create(cr, uid, self._prepare_order_line_procurement(cr, uid, order, line, move_ids and move_ids[-1] or move_id, date_planned, context=context))
                proc_ids.append(proc_id)
                line.write({'procurement_id': proc_id})
                for i_move_id in move_ids or [move_id]:
                    self.ship_recreate(cr, uid, order, line, i_move_id, proc_id)
            
            for i_picking_id in picking_ids or picking_id and [picking_id] or []:
                wf_service.trg_validate(uid, 'stock.picking', i_picking_id, 'button_confirm', cr)
        
        for proc_id in proc_ids:
            wf_service.trg_validate(uid, 'procurement.order', proc_id, 'button_confirm', cr)

        val = {}
        if order.state == 'shipping_except':
            val['state'] = 'progress'
            val['shipped'] = False

            if (order.order_policy == 'manual'):
                for line in order.order_line:
                    if (not line.invoiced) and (line.state not in ('cancel', 'draft')):
                        val['state'] = 'manual'
                        break
        order.write(val)
        return True

sale()

