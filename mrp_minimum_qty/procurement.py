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

from openerp import SUPERUSER_ID
from openerp import api, models
from openerp.tools.translate import _

class procurement_order(models.Model):
    _inherit = 'procurement.order'

    def make_mo(self, cr, uid, ids, context=None):
        """ Make Manufacturing(production) order from procurement
        @return: New created Production Orders procurement wise
        """
        res = {i: False for i in ids}
        production_obj = self.pool.get('mrp.production')
        bom_obj = self.pool.get('mrp.bom')
        uom_obj = self.pool.get('product.uom')
        proposed_mos = {}
        confirmed_procurements = set()
        for procurement in self.browse(cr, uid, ids, context=context):
            bom_id = procurement.bom_id.id
            if not bom_id:
                properties = [x.id for x in procurement.property_ids]
                bom_id = bom_obj._bom_find(cr, uid, product_id=procurement.product_id.id,
                                           properties=properties, context=context)
            if not bom_id:
                self.message_post(cr, uid, [procurement.id], body=_("No BoM exists for this product!"), context=context)
                continue

            if procurement.state == 'confirmed':
                confirmed_procurements.add(procurement.id)

            group_key = (procurement.company_id.id, bom_id, procurement.location_id.id)
            proposed_mos.setdefault(group_key, []).append((procurement.id, self._prepare_mo_vals(cr, uid, procurement, context=context)))

        for (company_id, bom_id, location_id), mo_vals in proposed_mos.iteritems():
            bom = bom_obj.browse(cr, uid, [bom_id], context=context)
            product_uom = bom.product_tmpl_id.uom_id.id

            requested_qty = 0
            procurements = []
            origin = []
            for procurement_id, proposed_mo in mo_vals:
                uom = proposed_mo['product_uom']
                qty = proposed_mo['product_qty']
                if uom != product_uom:
                    qty = uom_obj._compute_qty(cr, uid, uom, qty, product_uom)
                requested_qty += qty

                procurements.append(procurement_id)
                if proposed_mo['origin']:
                    origin.append(proposed_mo['origin'])
            origin = ",".join(origin) or False

            requested_qty = uom_obj._compute_qty(cr, uid, product_uom, requested_qty, bom.product_uom.id)
            if bom.minimum_qty > requested_qty:
                to_note = list(confirmed_procurements & set(procurements))
                if to_note:
                    self.message_post(cr, uid, to_note, body=_("Minimum manufacturing quantity of not met"), context=context)
                continue

            date_planned = False
            for procurement in self.browse(cr, uid, procurements, context=context):
                planned = self._get_date_planned(cr, uid, procurement, context=context)
                if not date_planned or planned < date_planned:
                    date_planned = planned

            #create the MO as SUPERUSER because the current user may not have the rights to do it (mto product launched by a sale for example)
            proposed_mo['origin'] = origin
            proposed_mo['date_planned'] = date_planned
            proposed_mo['product_qty'] = requested_qty
            proposed_mo['product_uom'] = product_uom
            proposed_mo['procurement_ids'] = [(6, 0, procurements)]

            produce_id = production_obj.create(cr, SUPERUSER_ID, proposed_mo, context=context)
            for procurement_id in procurements:
                res[procurement_id] = produce_id

            self.production_order_create_note(cr, uid, procurement, context=context)
            production_obj.action_compute(cr, uid, [produce_id], properties=[x.id for x in procurement.property_ids])
            production_obj.signal_workflow(cr, uid, [produce_id], 'button_confirm')
        return res

    @api.multi
    def run(self, autocommit=False):
        res = super(procurement_order, self).run(autocommit=autocommit)
        potential_mos = self.filtered(lambda x: x.state == 'exception'
                                                and x.rule_id
                                                and x.rule_id.action == 'manufacture')
        if not potential_mos:
            return res
        products = potential_mos.mapped('product_id')
        to_check = self.search([
                                ('state','=','exception'),
                                ('rule_id.action','=','manufacture'),
                                ('product_id', 'in', products._ids),
                                ])
        result = self.make_mo(to_check)
        processed = self.browse([i for i in result if result[i]])
        processed.write({'state': 'running'})
        return res
