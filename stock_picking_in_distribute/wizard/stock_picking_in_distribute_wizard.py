# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 credativ Ltd (<http://credativ.co.uk>).
#    All Rights Reserved
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

from osv import osv, fields
from tools.translate import _
from collections import defaultdict
import time

import openerp.addons.decimal_precision as dp
from openerp.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT
from openerp.tools.float_utils import float_compare
from openerp import netsvc


class StockPickingInDistributeWizard(osv.osv_memory):
    _name = "stock.picking.in.distribute_wizard"
    _description = "Distribute Incoming Moves"
    _columns = {
        'picking_id': fields.many2one('stock.picking', required=True),
        'products_remaining': fields.one2many('stock.picking.in.distribute_wizard.products_remaining', 'wizard_id', 'Remaining products for distribution'),
        'distribution_moves': fields.one2many('stock.picking.in.distribute_wizard.lines', 'wizard_id', 'Distribution Moves'),
        'location_id': fields.many2one('stock.location', 'Source Location', required=True),
        'supplier_location_id': fields.many2one('stock.location', 'Supplier Location', required=True),
        'date': fields.datetime('Date', required=True),
        }

    def default_get(self, cr, uid, fields, context):
        picking_id = context and context.get('active_id', False) or False
        if not picking_id:
            raise osv.except_osv(_('Error!'), _("No picking ID found. This action must be triggered with an active picking."))
        res = super(StockPickingInDistributeWizard, self).default_get(cr, uid, fields, context=context)
        # Populate moves left to distribute
        pick_obj = self.pool.get('stock.picking')
        picking = pick_obj.browse(cr, uid, picking_id, context=context)
        location_id = False
        to_distribute = {}
        for move in picking.move_lines:
            key = move.product_id.id
            to_distribute[key] = to_distribute.setdefault(key, 0) + move.product_qty
            if not location_id:
                location_id = move.location_dest_id.id
        products_remaining = []
        for product_id, product_qty in to_distribute.iteritems():
            products_remaining.append((0, 0, {'product_id': product_id, 'product_qty': product_qty}))
        res.update({'picking_id': picking_id,
                    'products_remaining': products_remaining,
                    'location_id': location_id,
                    'supplier_location_id': picking.move_lines[0].location_id.id,
                    'date': time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)})
        return res

    def action_confirm(self, cr, uid, ids, context=None):
        assert len(ids) == 1, 'Partial picking processing may only be done one at a time.'
        wf_service = netsvc.LocalService("workflow")
        stock_picking = self.pool.get('stock.picking')
        stock_move = self.pool.get('stock.move')
        uom_obj = self.pool.get('product.uom')
        partial = self.browse(cr, uid, ids[0], context=context)
        picking_type = partial.picking_id.type
        seq_obj_name = 'stock.picking.' + picking_type
        partial_data = {
            'delivery_date': partial.date
        }
        internal_moves = []
        for wizard_line in partial.distribution_moves:
            line_uom = wizard_line.product_id.uom_id
            move_id = wizard_line.move_id.id

            # Quantiny must be Positive
            if wizard_line.product_qty < 0:
                raise osv.except_osv(_('Warning!'), _('Please provide proper Quantity.'))

            # Compute the quantity for respective wizard_line in the line uom (this just do the rounding if necessary)
            qty_in_line_uom = uom_obj._compute_qty(cr, uid, line_uom.id, wizard_line.product_qty, line_uom.id)

            if line_uom.factor and line_uom.factor != 0:
                if float_compare(qty_in_line_uom, wizard_line.product_qty, precision_rounding=line_uom.rounding) != 0:
                    raise osv.except_osv(_('Warning!'), _('The unit of measure rounding does not allow you to ship "%s %s", only rounding of "%s %s" is accepted by the Unit of Measure.') % (wizard_line.product_qty, line_uom.name, line_uom.rounding, line_uom.name))
            if move_id:
                # Check rounding Quantity.ex.
                # picking: 1kg, uom kg rounding = 0.01 (rounding to 10g),
                # partial delivery: 253g
                # => result= refused, as the qty left on picking would be 0.747kg and only 0.75 is accepted by the uom.
                initial_uom = wizard_line.product_id.uom_id
                # Compute the quantity for respective wizard_line in the initial uom
                qty_in_initial_uom = uom_obj._compute_qty(cr, uid, line_uom.id, wizard_line.product_qty, initial_uom.id)
                without_rounding_qty = (wizard_line.product_qty / line_uom.factor) * initial_uom.factor
                if float_compare(qty_in_initial_uom, without_rounding_qty, precision_rounding=initial_uom.rounding) != 0:
                    raise osv.except_osv(_('Warning!'), _('The rounding of the initial uom does not allow you to ship "%s %s", as it would let a quantity of "%s %s" to ship and only rounding of "%s %s" is accepted by the uom.') % (wizard_line.product_qty, line_uom.name, wizard_line.move_id.product_qty - without_rounding_qty, initial_uom.name, initial_uom.rounding, initial_uom.name))
            else:
                new_moves = []
                move_id = stock_move.create(cr, uid, {'name': self.pool.get('ir.sequence').get(cr, uid, seq_obj_name),
                                                      'product_id': wizard_line.product_id.id,
                                                      'product_qty': wizard_line.product_qty,
                                                      'product_uom': wizard_line.product_id.uom_id.id,
                                                      'location_id': partial.supplier_location_id.id,
                                                      'location_dest_id': partial.location_id.id,
                                                      'picking_id': partial.picking_id.id
                                                      }, context=context)
                new_moves.append(move_id)
                partial_data['move%s' % (move_id)] = {
                    'product_id': wizard_line.product_id.id,
                    'product_qty': wizard_line.product_qty,
                    'product_uom': wizard_line.product_id.uom_id.id,
                }

            if wizard_line.move_id and wizard_line.location_dest_id.id != partial.location_id.id:
                internal_moves.append((0, 0, {'name': self.pool.get('ir.sequence').get(cr, uid, seq_obj_name),
                                              'product_id': wizard_line.product_id.id,
                                              'product_qty': wizard_line.product_qty,
                                              'product_uom': wizard_line.product_id.uom_id.id,
                                              'location_id': partial.location_id.id,
                                              'location_dest_id': wizard_line.location_dest_id.id,
                                              }))

            partial_data['move%s' % (move_id)] = {
                'product_id': wizard_line.product_id.id,
                'product_qty': wizard_line.product_qty,
                'product_uom': wizard_line.product_id.uom_id.id,
            }

            if (picking_type == 'in') and (wizard_line.product_id.cost_method == 'average'):
                partial_data['move%s' % (wizard_line.move_id.id)].update(product_price=wizard_line.cost,
                                                                         product_currency=wizard_line.currency.id)

        # Create internal moves to move stock to different location
        if internal_moves:
            new_picking = stock_picking.copy(cr, uid, partial.picking_id.id,
                                             {
                                                 'move_lines': internal_moves,
                                                 'state': 'draft',
                                                 'type': 'internal',
                                                 })
            wf_service.trg_validate(uid, 'stock.picking', new_picking, 'button_confirm', cr)
            stock_picking.action_move(cr, uid, [new_picking], context=context)

        stock_picking.do_partial(cr, uid, [partial.picking_id.id],
                                 partial_data, context=context)
        return {'type': 'ir.actions.act_window_close'}

    def action_recompute(self, cr, uid, ids, context=None):
        picking = self.pool.get('stock.picking')

        try:
            picking_id = context['picking_id']
        except KeyError:
            pass

        prod_remain_list = []
        products_remaining = defaultdict(int)
        for move in picking.browse(cr, uid, picking_id, context=context).move_lines:
            products_remaining[move.product_id] += move.product_qty

        for wizard in self.browse(cr, uid, ids, context=context):
            for move in wizard.distribution_moves:
                products_remaining[move.product_id] -= move.product_qty

        cr.execute('DELETE FROM stock_picking_in_distribute_wizard_products_remaining WHERE wizard_id IN %s', (tuple(ids),))
        for product_id, product_qty in products_remaining.iteritems():
            prod_remain_list.append((0, 0, {'product_id': product_id.id,
                                            'product_qty': product_qty}))
        self.write(cr, uid, ids, {'products_remaining': prod_remain_list})
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': ids[0],
            'res_model': 'stock.picking.in.distribute_wizard',
            'target': 'new',
        }


class MultiMoveCreateWizardProductsRemaining(osv.osv_memory):
    _name = "stock.picking.in.distribute_wizard.products_remaining"
    _description = "Remaining products"
    _columns = {
        'wizard_id': fields.many2one('stock.picking.in.distribute_wizard', 'Move creation wizard', required=True, ondelete='cascade', readonly=True),
        'product_id': fields.many2one('product.product', 'Product', required=True),
        'product_qty': fields.float('Quantity', digits_compute=dp.get_precision('Product Unit of Measure'), required=True),
    }


class MultiMoveCreateWizardLines(osv.osv_memory):
    _name = "stock.picking.in.distribute_wizard.lines"
    _description = "Distribution moves"
    _columns = {
        'wizard_id': fields.many2one('stock.picking.in.distribute_wizard', 'Move creation wizard', required=True, ondelete='cascade', readonly=True),
        'product_id': fields.many2one('product.product', 'Product', required=True),
        'product_qty': fields.float('Quantity', digits_compute=dp.get_precision('Product Unit of Measure'), required=True),
        'location_dest_id': fields.many2one('stock.location',
                                            'Destination Location',
                                            required=True),
        'move_id': fields.many2one('stock.move',
                                   'Move',
                                   require=True)
        }

    _defaults = {
        'location_dest_id': lambda self, cr, uid, context: context.get('location_dest_id', False),
        }

    def _get_values(self, cr, uid, move, context=None):
        # TODO add support for product average price
        return {'product_id': move.product_id.id or None,
                'location_dest_id': move.location_dest_id.id or None,
                }

    def onchange_moves(self, cr, uid, ids, move_id, context=None):
        if context is None:
            context = {}

        res = {}
        if move_id:
            stock_move = self.pool.get('stock.move')
            move = stock_move.browse(cr, uid, move_id, context)
            res = self._get_values(cr, uid, move, context=context)

        return {'value': res}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
