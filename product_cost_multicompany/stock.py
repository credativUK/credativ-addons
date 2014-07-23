# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution   
#    Copyright (C) 2014 credativ ltd (<http://www.credativ.co.uk>). All Rights Reserved
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
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
from operator import itemgetter
from itertools import groupby
import netsvc

class StockPicking(osv.Model):
    _inherit = 'stock.picking'

    # FIXME: needs refactoring, this code is partially duplicated in stock_move.do_partial()!
    def do_partial(self, cr, uid, ids, partial_datas, context=None):
        """ Makes partial picking and moves done.
        @param partial_datas : Dictionary containing details of partial picking
                          like partner_id, partner_id, delivery_date,
                          delivery moves with product_id, product_qty, uom
        @return: Dictionary of values

        Overridden completly so that the qty_available is only taken from the current company warehouse
        """
        if context is None:
            context = {}
        else:
            context = dict(context)
        res = {}
        move_obj = self.pool.get('stock.move')
        product_obj = self.pool.get('product.product')
        currency_obj = self.pool.get('res.currency')
        uom_obj = self.pool.get('product.uom')
        sequence_obj = self.pool.get('ir.sequence')
        wf_service = netsvc.LocalService("workflow")
        location_obj = self.pool.get('stock.location')
        for pick in self.browse(cr, uid, ids, context=context):
            new_picking = None
            complete, too_many, too_few = [], [], []
            move_product_qty, prodlot_ids, product_avail, partial_qty, product_uoms = {}, {}, {}, {}, {}
            for move in pick.move_lines:
                if move.state in ('done', 'cancel'):
                    continue
                partial_data = partial_datas.get('move%s'%(move.id), {})
                product_qty = partial_data.get('product_qty',0.0)
                move_product_qty[move.id] = product_qty
                product_uom = partial_data.get('product_uom',False)
                product_price = partial_data.get('product_price',0.0)
                product_currency = partial_data.get('product_currency',False)
                prodlot_id = partial_data.get('prodlot_id')
                prodlot_ids[move.id] = prodlot_id
                product_uoms[move.id] = product_uom
                partial_qty[move.id] = uom_obj._compute_qty(cr, uid, product_uoms[move.id], product_qty, move.product_uom.id)
                if move.product_qty == partial_qty[move.id]:
                    complete.append(move)
                elif move.product_qty > partial_qty[move.id]:
                    too_few.append(move)
                else:
                    too_many.append(move)

                # Average price computation
                if (pick.type == 'in') and (move.product_id.cost_method == 'average') and (move.location_dest_id.company_id):
                    assert move.company_id.id == pick.company_id.id, "Move and picking company IDs do not match. Account moves cannot be created."
                    assert move.location_dest_id.company_id.id, "Internal picking must be going to a location owned by a company."
                    company = move.location_dest_id.company_id
                    loc_ids = location_obj.search(cr, uid,[('usage','=','internal'), ('company_id', '=', company.id)])
                    ctx = {'company_id': company.id, 'location': loc_ids}
                    product = product_obj.browse(cr, uid, move.product_id.id, context=ctx)
                    move_currency_id = company.currency_id.id
                    ctx['currency_id'] = move_currency_id
                    qty = uom_obj._compute_qty(cr, uid, product_uom, product_qty, product.uom_id.id)
                    price_type_currency_id = company.currency_id.id

                    if product.id not in product_avail:
                        # keep track of stock on hand including processed lines not yet marked as done
                        product_avail[product.id] = product.qty_available

                    if qty > 0:
                        # New price in company currency
                        new_price = currency_obj.compute(cr, uid, product_currency,
                                move_currency_id, product_price, round=False)
                        new_price = uom_obj._compute_price(cr, uid, product_uom, new_price,
                                product.uom_id.id)
                        if product_avail[product.id] <= 0:
                            product_avail[product.id] = 0
                            new_std_price = new_price
                        else:
                            # Get the standard price
                            amount_unit = product.standard_price
                            # Here we must convert the new price computed in the currency of the price_type
                            # of the product (e.g. company currency: EUR, price_type: USD)
                            # The current value is still in company currency at this stage
                            new_std_price = ((amount_unit * product_avail[product.id])\
                                + (new_price * qty))/(product_avail[product.id] + qty)
                        # Convert the price in price_type currency
                        new_std_price = currency_obj.compute(
                                cr, uid, move_currency_id,
                                price_type_currency_id, new_std_price)
                        # Write the field according to price type field
                        product_obj.write(cr, uid, [product.id], {'standard_price': new_std_price}, context=ctx)

                        # Record the values that were chosen in the wizard, so they can be
                        # used for inventory valuation if real-time valuation is enabled.
                        move_obj.write(cr, uid, [move.id],
                                {'price_unit': product_price,
                                 'price_currency_id': product_currency})

                        product_avail[product.id] += qty

            for move in too_few:
                product_qty = move_product_qty[move.id]
                if not new_picking:
                    new_picking_name = pick.name
                    self.write(cr, uid, [pick.id], 
                               {'name': sequence_obj.get(cr, uid,
                                            'stock.picking.%s'%(pick.type)),
                               })
                    new_picking = self.copy(cr, uid, pick.id,
                            {
                                'name': new_picking_name,
                                'move_lines' : [],
                                'state':'draft',
                            })
                if product_qty != 0:
                    defaults = {
                            'product_qty' : product_qty,
                            'product_uos_qty': product_qty, #TODO: put correct uos_qty
                            'picking_id' : new_picking,
                            'state': 'assigned',
                            'move_dest_id': move.move_dest_id.id,
                            'price_unit': move.price_unit,
                            'product_uom': product_uoms[move.id]
                    }
                    prodlot_id = prodlot_ids[move.id]
                    if prodlot_id:
                        defaults.update(prodlot_id=prodlot_id)
                    move_obj.copy(cr, uid, move.id, defaults)
                move_obj.write(cr, uid, [move.id],
                        {
                            'product_qty': move.product_qty - partial_qty[move.id],
                            'product_uos_qty': move.product_qty - partial_qty[move.id], #TODO: put correct uos_qty
                            'prodlot_id': False,
                            'tracking_id': False,
                        })

            if new_picking:
                move_obj.write(cr, uid, [c.id for c in complete], {'picking_id': new_picking})
            for move in complete:
                defaults = {'product_uom': product_uoms[move.id], 'product_qty': move_product_qty[move.id]}
                if prodlot_ids.get(move.id):
                    defaults.update({'prodlot_id': prodlot_ids[move.id]})
                move_obj.write(cr, uid, [move.id], defaults)
            for move in too_many:
                product_qty = move_product_qty[move.id]
                defaults = {
                    'product_qty' : product_qty,
                    'product_uos_qty': product_qty, #TODO: put correct uos_qty
                    'product_uom': product_uoms[move.id]
                }
                prodlot_id = prodlot_ids.get(move.id)
                if prodlot_ids.get(move.id):
                    defaults.update(prodlot_id=prodlot_id)
                if new_picking:
                    defaults.update(picking_id=new_picking)
                move_obj.write(cr, uid, [move.id], defaults)

            # At first we confirm the new picking (if necessary)
            if new_picking:
                wf_service.trg_validate(uid, 'stock.picking', new_picking, 'button_confirm', cr)
                # Then we finish the good picking
                self.write(cr, uid, [pick.id], {'backorder_id': new_picking})
                self.action_move(cr, uid, [new_picking], context=context)
                wf_service.trg_validate(uid, 'stock.picking', new_picking, 'button_done', cr)
                wf_service.trg_write(uid, 'stock.picking', pick.id, cr)
                delivered_pack_id = pick.id
                back_order_name = self.browse(cr, uid, delivered_pack_id, context=context).name
                self.message_post(cr, uid, new_picking, body=_("Back order <em>%s</em> has been <b>created</b>.") % (back_order_name), context=context)
            else:
                self.action_move(cr, uid, [pick.id], context=context)
                wf_service.trg_validate(uid, 'stock.picking', pick.id, 'button_done', cr)
                delivered_pack_id = pick.id

            delivered_pack = self.browse(cr, uid, delivered_pack_id, context=context)
            res[pick.id] = {'delivered_picking': delivered_pack.id or False}

        return res

class StockMove(osv.Model):
    _inherit = 'stock.move'

    # FIXME: needs refactoring, this code is partially duplicated in stock_picking.do_partial()!
    def do_partial(self, cr, uid, ids, partial_datas, context=None):
        """ Makes partial pickings and moves done.
        @param partial_datas: Dictionary containing details of partial picking
                          like partner_id, delivery_date, delivery
                          moves with product_id, product_qty, uom

        Overridden completly so that the qty_available is only taken from the current company warehouse
        """
        res = {}
        picking_obj = self.pool.get('stock.picking')
        product_obj = self.pool.get('product.product')
        currency_obj = self.pool.get('res.currency')
        pricetype_obj = self.pool.get('product.price.type')
        uom_obj = self.pool.get('product.uom')
        wf_service = netsvc.LocalService("workflow")
        location_obj = self.pool.get('stock.location')

        if context is None:
            context = {}

        complete, too_many, too_few = [], [], []
        move_product_qty = {}
        prodlot_ids = {}
        for move in self.browse(cr, uid, ids, context=context):
            if move.state in ('done', 'cancel'):
                continue
            partial_data = partial_datas.get('move%s'%(move.id), False)
            assert partial_data, _('Missing partial picking data for move #%s.') % (move.id)
            product_qty = partial_data.get('product_qty',0.0)
            move_product_qty[move.id] = product_qty
            product_uom = partial_data.get('product_uom',False)
            product_price = partial_data.get('product_price',0.0)
            product_currency = partial_data.get('product_currency',False)
            prodlot_ids[move.id] = partial_data.get('prodlot_id')
            if move.product_qty == product_qty:
                complete.append(move)
            elif move.product_qty > product_qty:
                too_few.append(move)
            else:
                too_many.append(move)

            # Average price computation
            if (move.picking_id.type == 'in') and (move.product_id.cost_method == 'average'):
                assert move.location_dest_id.company_id.id, "Internal picking must be going to a location owned by a company."
                company = move.location_dest_id.company_id
                loc_ids = location_obj.search(cr, uid,[('usage','=','internal'), ('company_id', '=', company.id)])
                ctx = {'company_id': company.id, 'location': loc_ids}

                product = product_obj.browse(cr, uid, move.product_id.id, context=ctx)
                move_currency_id = company.currency_id.id
                ctx['currency_id'] = move_currency_id
                qty = uom_obj._compute_qty(cr, uid, product_uom, product_qty, product.uom_id.id)
                price_type_currency_id = company.currency_id.id
                if qty > 0:
                    new_price = currency_obj.compute(cr, uid, product_currency,
                            move_currency_id, product_price, round=False)
                    new_price = uom_obj._compute_price(cr, uid, product_uom, new_price,
                            product.uom_id.id)
                    if product.qty_available <= 0:
                        new_std_price = new_price
                    else:
                        # Get the standard price
                        amount_unit = product.standard_price
                        # Here we must convert the new price computed in the currency of the price_type
                        # of the product (e.g. company currency: EUR, price_type: USD)
                        # The current value is still in company currency at this stage
                        new_std_price = ((amount_unit * product.qty_available)\
                            + (new_price * qty))/(product.qty_available + qty)
                    # Convert the price in price_type currency
                    new_std_price = currency_obj.compute(
                            cr, uid, move_currency_id,
                            price_type_currency_id, new_std_price)
                    # Write the field according to price type field
                    product_obj.write(cr, uid, [product.id],{'standard_price': new_std_price}, context=ctx)

                    # Record the values that were chosen in the wizard, so they can be
                    # used for inventory valuation if real-time valuation is enabled.
                    self.write(cr, uid, [move.id],
                                {'price_unit': product_price,
                                 'price_currency_id': product_currency,
                                })

        for move in too_few:
            product_qty = move_product_qty[move.id]
            if product_qty != 0:
                defaults = {
                            'product_qty' : product_qty,
                            'product_uos_qty': product_qty,
                            'picking_id' : move.picking_id.id,
                            'state': 'assigned',
                            'move_dest_id': move.move_dest_id.id,
                            'price_unit': move.price_unit,
                            }
                prodlot_id = prodlot_ids[move.id]
                if prodlot_id:
                    defaults.update(prodlot_id=prodlot_id)
                new_move = self.copy(cr, uid, move.id, defaults)
                complete.append(self.browse(cr, uid, new_move))
            self.write(cr, uid, [move.id],
                    {
                        'product_qty': move.product_qty - product_qty,
                        'product_uos_qty': move.product_qty - product_qty,
                        'prodlot_id': False,
                        'tracking_id': False,
                    })


        for move in too_many:
            self.write(cr, uid, [move.id],
                    {
                        'product_qty': move.product_qty,
                        'product_uos_qty': move.product_qty,
                    })
            complete.append(move)

        for move in complete:
            if prodlot_ids.get(move.id):
                self.write(cr, uid, [move.id],{'prodlot_id': prodlot_ids.get(move.id)})
            self.action_done(cr, uid, [move.id], context=context)
            if  move.picking_id.id :
                # TOCHECK : Done picking if all moves are done
                cr.execute("""
                    SELECT move.id FROM stock_picking pick
                    RIGHT JOIN stock_move move ON move.picking_id = pick.id AND move.state = %s
                    WHERE pick.id = %s""",
                            ('done', move.picking_id.id))
                res = cr.fetchall()
                if len(res) == len(move.picking_id.move_lines):
                    picking_obj.action_move(cr, uid, [move.picking_id.id])
                    wf_service.trg_validate(uid, 'stock.picking', move.picking_id.id, 'button_done', cr)

        return [move.id for move in complete]

    def _get_reference_accounting_values_for_valuation(self, cr, uid, move, context=None):
        res = super(StockMove, self)._get_reference_accounting_values_for_valuation(cr, uid, move, context=context)
        default_uom = move.product_id.uom_id.id
        company = move.location_id.company_id or move.location_dest_id.company_id or move.company_id
        reference_currency_id = company.currency_id.id
        if not (move.product_id.cost_method == 'average' and move.price_unit):
            qty = self.pool.get('product.uom')._compute_qty(cr, uid, move.product_uom.id, move.product_qty, default_uom)
            product = self.pool.get('product.product').browse(cr, uid, move.product_id.id, context={'company_id': company.id})
            amount_unit = product.standard_price
            reference_amount = amount_unit * qty
            return reference_amount, reference_currency_id
        return res

class StockPartialPicking(osv.TransientModel):
    _inherit = 'stock.partial.picking'

    def _product_cost_for_average_update(self, cr, uid, move):
        # If we have a purchase, use this for cost
        if move.picking_id.purchase_id:
            return {'cost': move.purchase_line_id.price_unit,
                    'currency': move.picking_id.purchase_id.pricelist_id.currency_id.id}
        # Otherwise take our standard_price from the company of the stock move (if transfer between companies, this will be the source company)
        company = move.location_id.company_id or move.location_dest_id.company_id or move.company_id
        product = self.pool.get('product.product').browse(cr, uid, move.product_id.id, context={'company_id': company.id})
        return {'cost': product.standard_price, 'currency': company.currency_id.id}

class StockLocation(osv.Model):
    _inherit = 'stock.location'

    def _product_value(self, cr, uid, ids, field_names, arg, context=None):
        """Computes stock value (real and virtual) for a product, as well as stock qty (real and virtual).
        @param field_names: Name of field
        @return: Dictionary of values

        Overridden completly so that the product is read with the correct standard price
        """
        prod_id = context and context.get('product_id', False)

        if not prod_id:
            return dict([(i, {}.fromkeys(field_names, 0.0)) for i in ids])

        product_product_obj = self.pool.get('product.product')

        cr.execute('select distinct product_id, location_id from stock_move where location_id in %s', (tuple(ids), ))
        dict1 = cr.dictfetchall()
        cr.execute('select distinct product_id, location_dest_id as location_id from stock_move where location_dest_id in %s', (tuple(ids), ))
        dict2 = cr.dictfetchall()
        res_products_by_location = sorted(dict1+dict2, key=itemgetter('location_id'))
        products_by_location = dict((k, [v['product_id'] for v in itr]) for k, itr in groupby(res_products_by_location, itemgetter('location_id')))

        result = dict([(i, {}.fromkeys(field_names, 0.0)) for i in ids])
        result.update(dict([(i, {}.fromkeys(field_names, 0.0)) for i in list(set([aaa['location_id'] for aaa in res_products_by_location]))]))

        currency_id = self.pool.get('res.users').browse(cr, uid, uid).company_id.currency_id.id
        currency_obj = self.pool.get('res.currency')
        user_company = self.pool.get('res.users').browse(cr, uid, uid).company_id
        for loc_id, product_ids in products_by_location.items():
            if prod_id:
                product_ids = [prod_id]
            location = self.browse(cr, uid, loc_id)
            company = location.company_id or user_company
            currency = company.currency
            c = (context or {}).copy()
            c['location'] = loc_id
            c['company_id'] = company.id
            for prod in product_product_obj.browse(cr, uid, product_ids, context=c):
                for f in field_names:
                    if f == 'stock_real':
                        if loc_id not in result:
                            result[loc_id] = {}
                        result[loc_id][f] += prod.qty_available
                    elif f == 'stock_virtual':
                        result[loc_id][f] += prod.virtual_available
                    elif f == 'stock_real_value':
                        amount = prod.qty_available * prod.standard_price
                        amount = currency_obj.round(cr, uid, currency, amount)
                        result[loc_id][f] += amount
                    elif f == 'stock_virtual_value':
                        amount = prod.virtual_available * prod.standard_price
                        amount = currency_obj.round(cr, uid, currency, amount)
                        result[loc_id][f] += amount
        return result

class StockLocation(osv.Model):
    _inherit = 'stock.location'

    def picking_type_get(self, cr, uid, from_location, to_location, context=None):
        # Use chained picking type if one available
        if from_location.chained_picking_type:
            res = from_location.chained_picking_type
        else:
            res = super(StockLocation, self).picking_type_get(cr, uid, from_location, to_location, context=context)
        return res

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
