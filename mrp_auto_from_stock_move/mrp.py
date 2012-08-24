# -*- coding: utf-8 -*-
from osv import fields,osv
from tools.translate import _
import netsvc
import time

class mrp_bom(osv.osv):
    _inherit = 'mrp.bom'

    _columns = {
        'type': fields.selection([('normal','Normal BoM'),('phantom','Sets / Phantom'),('automatic','Automatic')], 'BoM Type', required=True,
                                 help= "If a sub-product is used in several products, it can be useful to create its own BoM. "\
                                 "Though if you don't want separated production orders for this sub-product, select Set/Phantom as BoM type. "\
                                 "If a Phantom BoM is used for a root product, it will be sold and shipped as a set of components, instead of being produced."),

    }

mrp_bom()

class mrp_production(osv.osv):
    _inherit = 'mrp.production'

    _columns = {
        'incoming_shipment_id': fields.many2one('stock.picking', 'Incoming Shipment', readonly=True, help='This is the Incoming Shipment List to process the finished goods move'),
    }

    def _make_production_incoming_shipment(self, cr, uid, production, context=None):
        ir_sequence = self.pool.get('ir.sequence')
        stock_picking = self.pool.get('stock.picking')
        routing_loc = None
        pick_type = 'in'
        address_id = False

        # Take routing address as a Shipment Address.
        if production.bom_id.routing_id and production.bom_id.routing_id.location_id:
            routing_loc = production.bom_id.routing_id.location_id
            address_id = routing_loc.address_id and routing_loc.address_id.id or False

        # Take next Sequence number of shipment base on type
        pick_name = ir_sequence.get(cr, uid, 'stock.picking.' + pick_type)

        picking_id = stock_picking.create(cr, uid, {
            'name': pick_name,
            'origin': (production.origin or '').split(':')[0] + ':' + production.name,
            'type': pick_type,
            'move_type': 'one',
            'state': 'draft',
            'address_id': address_id,
            'auto_picking': self._get_auto_picking(cr, uid, production),
            'company_id': production.company_id.id,
        })
        production.write({'incoming_shipment_id': picking_id}, context=context)
        return picking_id

    def action_confirm(self, cr, uid, ids):
        picking_id = super(mrp_production, self).action_confirm(cr, uid, ids)
        for production in self.browse(cr, uid, ids):
            #Perform only if bom_type is automatic
            if production.bom_id and production.bom_id.type == 'automatic':
                shipment_id = self._make_production_incoming_shipment(cr, uid, production)
                for production_line in production.move_created_ids:
                    # Internal shipment is created for Stockable and Consumer Products
                    if production_line.product_id.type in ('product', 'consu'):
                        production_line.write({'picking_id': shipment_id})
        return picking_id

    def test_subcontractor_product(self, cr, uid, ids):
        """ Tests whether the product being made is of bom type automatic and consumes the raw materials if so.
        @return: True or False
        """
        wf_service = netsvc.LocalService("workflow")
        prod_obj = self.pool.get('mrp.production')
        move_obj = self.pool.get('stock.move')
        res = False
        prod_items = prod_obj.browse(cr, uid, ids)
        for prod in prod_items:
            if prod.bom_id and prod.bom_id.type == 'automatic':
                res = True
                for move_id in prod.move_lines:
                    move_obj.action_consume(cr, uid, [move_id.id],move_id.product_qty, move_id.location_id.id)
                    wf_service.trg_validate(uid, 'stock.picking', prod.incoming_shipment_id.id, 'button_confirm', cr)
        return res


mrp_production()

class stock_picking(osv.osv):
    _inherit = 'stock.picking'

    def change_mo_state(self, cr, uid, ids, context=None):
        wf_service = netsvc.LocalService("workflow")
        prod_obj = self.pool.get('mrp.production')
        #Change the MO state to done when the incoming shipment for finished product is changed to done!
        #check if there is any MO related to finished product moves picking
        production_ids = prod_obj.search(cr, uid, [('incoming_shipment_id','in',ids),('state','not in',['draft','done','cancel'])])
        if production_ids:
            for prod in prod_obj.browse(cr, uid, production_ids):
                if prod.bom_id and prod.bom_id.type == 'automatic':
                    wf_service.trg_validate(uid, 'mrp.production', prod.id, 'button_produce_done', cr)
        return True

    def action_done(self, cr, uid, ids, context=None):
        """ Changes picking state to done.
        @return: True
        """
        res = super(stock_picking,self).action_done(cr, uid, ids, context=context)
        self.change_mo_state(cr, uid, ids, context=context)
        return res

stock_picking()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: