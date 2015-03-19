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

from openerp.tests import common
from openerp.addons.stock.tests.common import TestStockCommon

class TestMOMerging(TestStockCommon):
    def setUp(self):
        super(TestMOMerging, self).setUp()
        self.ProcurementObj = self.env['procurement.order']
        self.ManufaturingObj = self.env['mrp.production']
        self.RouteObj = self.env['stock.location.route']
        self.BoMObj = self.env['mrp.bom']

        self.manufacturing_route = self.env.ref('mrp.route_warehouse0_manufacture')
        self.manufacturing_rule = self.manufacturing_route.pull_ids[0]

        self.uom_minimum = self.BoMObj.create({
            'name': 'BoM with minimum Qty',
            'product_tmpl_id': self.productA.product_tmpl_id.id,
            'minimum_qty': 15,
        })

    def test_00_minimum_manuf_qty_satisfied(self):
        self.procurement_enough = self.ProcurementObj.create({
            'name': 'Sizeable procurement',
            'product_id': self.productA.id,
            'product_qty': 20,
            'product_uom': self.productA.uom_id.id,
            'location_id': self.stock_location,
            'rule_id': self.manufacturing_rule.id,
            'state': 'confirmed',
        })
        self.ProcurementObj.run_scheduler()
        planned_mos = self.ManufaturingObj.search([('bom_id','=',self.uom_minimum.id)])
        self.assertEqual(len(planned_mos), 1, "Wrong number of manufacturing orders created.")
        self.assertEqual(planned_mos[0].procurement_ids, self.procurement_enough, "Unexpected procurement assigned to MO.")
        self.assertEqual(self.procurement_enough.state, "running", "Unexpected state of the processed procurement")

    def test_10_minimum_manuf_qty_not_satisfied(self):
        self.procurement_too_small = self.ProcurementObj.create({
            'name': 'Small procurement',
            'product_id': self.productA.id,
            'product_qty': 5,
            'product_uom': self.productA.uom_id.id,
            'location_id': self.stock_location,
            'rule_id': self.manufacturing_rule.id,
            'state': 'confirmed',
        })

        self.ProcurementObj.run_scheduler()
        planned_mos = self.ManufaturingObj.search([('bom_id','=',self.uom_minimum.id)])
        self.assertEqual(len(planned_mos), 0, "Wrong number of manufacturing orders created.")
        self.assertEqual(self.procurement_too_small.state, "exception", "Unexpected state of the unprocessed procurement")

    def test_20_mo_merge(self):
        self.procurement_too_small = self.ProcurementObj.create({
            'name': 'Small procurement',
            'product_id': self.productA.id,
            'product_qty': 5,
            'product_uom': self.productA.uom_id.id,
            'location_id': self.stock_location,
            'rule_id': self.manufacturing_rule.id,
            'state': 'confirmed',
        })
        self.ProcurementObj.run_scheduler()
        self.assertEqual(self.procurement_too_small.state, "exception", "Unexpected state of the unprocessed procurement")

        self.procurement_dozen = self.ProcurementObj.create({
            'name': 'Second small procurement',
            'product_id': self.productA.id,
            'product_qty': 1,
            'product_uom': self.uom_dozen.id,
            'location_id': self.stock_location,
            'rule_id': self.manufacturing_rule.id,
            'state': 'confirmed',
        })

        self.ProcurementObj.run_scheduler()
        planned_mos = self.ManufaturingObj.search([('bom_id','=',self.uom_minimum.id)])
        self.assertEqual(len(planned_mos), 1, "Wrong number of manufacturing orders created.")
        self.assertEqual(set(planned_mos[0].procurement_ids), {self.procurement_too_small, self.procurement_dozen}, "Unexpected procurement assigned to MO.")
        self.assertEqual(self.procurement_too_small.state, "running", "Unexpected state of the processed procurement")
        self.assertEqual(self.procurement_dozen.state, "running", "Unexpected state of the processed procurement")
