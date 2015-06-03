# -*- coding: utf-8 -*-
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

from openerp import api, models, fields, _

class mrp_bom(models.Model):
    _inherit = 'mrp.bom'

    minimum_qty = fields.Float('Minimum Qty', help="Minimum manufacturing quantity for this BoM")

class mrp_production(models.Model):
    _inherit = 'mrp.production'

    procurement_ids = fields.One2many('procurement.order', 'production_id', 'Procurements', copy=False, readonly=True)

    def _make_production_produce_line(self, cr, uid, production, context=None):
        stock_move = self.pool.get('stock.move')
        proc_obj = self.pool.get('procurement.order')
        uom_obj = self.pool.get("product.uom")
        source_location_id = production.product_id.property_stock_production.id
        destination_location_id = production.location_dest_id.id
        procs = proc_obj.search(cr, uid, [('production_id', '=', production.id)], context=context)
        procurements = procs and\
            proc_obj.browse(cr, uid, procs, context=context) or [False]
        for procurement in procurements:
            date_planned = procurement and proc_obj._get_date_planned(cr, uid, procurement, context=context) or production.date_planned
            product_qty = production.product_qty
            if procurement:
                # code elsewhere expects all moves for the same product to have
                # the same uom, convert
                product_qty = uom_obj._compute_qty(cr, uid,
                                                   procurement.product_uom.id,
                                                   procurement.product_qty,
                                                   production.product_uom.id)
            data = {
                'name': production.name,
                'date': date_planned,
                'product_id': production.product_id.id,
                'product_uom': production.product_uom.id,
                'product_uom_qty': product_qty,
                'product_uos_qty': (procurement and procurement.product_uos and procurement.product_uos_qty) \
                                    or (production.product_uos and production.product_uos_qty) \
                                    or False,
                'product_uos': (procurement and procurement.product_uos and procurement.product_uos.id) \
                                or (production.product_uos and production.product_uos.id) \
                                or False,
                'location_id': source_location_id,
                'location_dest_id': destination_location_id,
                'move_dest_id': (procurement and procurement.move_dest_id and procurement.move_dest_id.id) or production.move_prod_id.id,
                'procurement_id': procurement and procurement.id,
                'company_id': production.company_id.id,
                'production_id': production.id,
                'origin': production.name,
                'group_id': procurement and procurement.group_id.id,
            }
            move_id = stock_move.create(cr, uid, data, context=context)
            stock_move.action_confirm(cr, uid, [move_id], context=context)

    def action_produce(self, cr, uid, production_id, production_qty, production_mode, wiz=False, context=None):
        """ To produce final product based on production mode (consume/consume&produce).
        If Production mode is consume, all stock move lines of raw materials will be done/consumed.
        If Production mode is consume & produce, all stock move lines of raw materials will be done/consumed
        and stock move lines of final product will be also done/produced.
        @param production_id: the ID of mrp.production object
        @param production_qty: specify qty to produce in the uom of the production order
        @param production_mode: specify production mode (consume/consume&produce).
        @param wiz: the mrp produce product wizard, which will tell the amount of consumed products needed
        @return: True
        """
        stock_mov_obj = self.pool.get('stock.move')
        uom_obj = self.pool.get("product.uom")
        production = self.browse(cr, uid, production_id, context=context)
        production_qty_uom = uom_obj._compute_qty(cr, uid, production.product_uom.id, production_qty, production.product_id.uom_id.id)

        main_production_move = False
        if production_mode == 'consume_produce':
            remaining_qty = {}
            template_move = {}

            # assess how much should be produced
            for produce_product in production.move_created_ids:
                subproduct_factor = self._get_subproduct_factor(cr, uid, production.id, produce_product.id, context=context)
                lot_id = False
                if wiz:
                    lot_id = wiz.lot_id.id

                remaining_qty.setdefault(produce_product.product_id.id, subproduct_factor * production_qty_uom)

                consumed_qty = min(produce_product.product_qty, remaining_qty[produce_product.product_id.id])
                if consumed_qty > 0:
                    new_moves = stock_mov_obj.action_consume(cr, uid, [produce_product.id], consumed_qty,
                                                            location_id=produce_product.location_id.id, restrict_lot_id=lot_id, context=context)
                    stock_mov_obj.write(cr, uid, new_moves, {'production_id': production_id}, context=context)

                remaining_qty[produce_product.product_id.id] -= produce_product.product_qty
                template_move[produce_product.product_id.id] = produce_product.id

                if produce_product.product_id.id == production.product_id.id:
                    main_production_move = produce_product.id

            for product_id in remaining_qty:
                if remaining_qty[product_id] < 0: # In case you need to make more than planned
                    #consumed more in wizard than previously planned
                    extra_move_id = stock_mov_obj.copy(cr, uid, template_move[product_id], default={'product_uom_qty': -remaining_qty[product_id],
                                                                                                    'production_id': production_id}, context=context)
                    stock_mov_obj.action_confirm(cr, uid, [extra_move_id], context=context)
                    stock_mov_obj.action_done(cr, uid, [extra_move_id], context=context)

        if production_mode in ['consume', 'consume_produce']:
            if wiz:
                consume_lines = []
                for cons in wiz.consume_lines:
                    consume_lines.append({'product_id': cons.product_id.id, 'lot_id': cons.lot_id.id, 'product_qty': cons.product_qty})
            else:
                consume_lines = self._calculate_qty(cr, uid, production, production_qty_uom, context=context)
            for consume in consume_lines:
                remaining_qty = consume['product_qty']
                for raw_material_line in production.move_lines:
                    if raw_material_line.state in ('done', 'cancel'):
                        continue
                    if remaining_qty <= 0:
                        break
                    if consume['product_id'] != raw_material_line.product_id.id:
                        continue
                    consumed_qty = min(remaining_qty, raw_material_line.product_qty)
                    stock_mov_obj.action_consume(cr, uid, [raw_material_line.id], consumed_qty, raw_material_line.location_id.id,
                                                 restrict_lot_id=consume['lot_id'], consumed_for=main_production_move, context=context)
                    remaining_qty -= consumed_qty
                if remaining_qty:
                    #consumed more in wizard than previously planned
                    product = self.pool.get('product.product').browse(cr, uid, consume['product_id'], context=context)
                    extra_move_id = self._make_consume_line_from_data(cr, uid, production, product, product.uom_id.id, remaining_qty, False, 0, context=context)
                    stock_mov_obj.write(cr, uid, [extra_move_id], {'restrict_lot_id': consume['lot_id'],
                                                                    'consumed_for': main_production_move}, context=context)
                    stock_mov_obj.action_done(cr, uid, [extra_move_id], context=context)

        self.message_post(cr, uid, production_id, body=_("%s produced") % self._description, context=context)
        self.signal_workflow(cr, uid, [production_id], 'button_produce_done')
        return True

    def product_id_change(self, cr, uid, ids, product_id, product_qty=0, context=None):
        res = super(mrp_production, self).product_id_change(cr, uid, ids, product_id=product_id, product_qty=product_qty, context=context)
        if not res['value']['bom_id']:
            return res

        value = res['value']

        uom_obj = self.pool.get('product.uom')

        bom = self.pool.get('mrp.bom').browse(cr, uid, value['bom_id'])
        product_qty = value.get('product_qty', product_qty)

        requested_qty = uom_obj._compute_qty(cr, uid, value['product_uom'], product_qty, bom.product_uom.id)
        if requested_qty < bom.minimum_qty:
            res['warning'] = {'title': _('Warning'), 'message': _("The minimum manufacturing quantity is not met, rules for this BoM say the minimum is {} {}.").format(bom.minimum_qty, bom.product_uom.name)}

        return res

    def bom_id_change(self, cr, uid, ids, bom_id, product_uom=False, product_qty=0, context=None):
        uom_obj = self.pool.get('product.uom')

        res = super(mrp_production, self).bom_id_change(cr, uid, ids, bom_id=bom_id, context=context)
        value = res['value']

        bom = self.pool.get('mrp.bom').browse(cr, uid, value.get('bom_id', bom_id))
        product_uom = value.get('product_uom', product_uom)
        product_qty = value.get('product_qty', product_qty)

        requested_qty = uom_obj._compute_qty(cr, uid, product_uom, product_qty, bom.product_uom.id)
        if requested_qty < bom.minimum_qty:
            res['warning'] = {'title': _('Warning'), 'message': _("The minimum manufacturing quantity is not met, rules for this BoM say the minimum is {} {}.").format(bom.minimum_qty, bom.product_uom.name)}

        return res

    # unused as most views already define their own onchange
    @api.onchange("product_qty", "product_uom", "bom_id")
    def _onchange_product_qty(self):
        for production in self:
            if not production.bom_id:
                continue
            requested_qty = production.env['product.uom']._compute_qty(production.product_uom.id, production.product_qty, production.bom_id.product_uom.id)
            if requested_qty < production.bom_id.minimum_qty:
                production.message = _("The minimum manufacturing quantity is not met, rules for this BoM say the minimum is {} {}.").format(production.bom_id.minimum_qty, production.bom_id.product_uom.name)
