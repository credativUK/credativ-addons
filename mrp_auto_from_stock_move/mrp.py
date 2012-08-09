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
#                        stock_move.write(cr, uid, [production_line.id], {'picking_id': shipment_id})
        
        return picking_id
    
mrp_production()

class stock_picking(osv.osv):
    _inherit = 'stock.picking'
    
    def change_mo_state(self, cr, uid, ids, context=None):
        wf_service = netsvc.LocalService("workflow")
        prod_obj = self.pool.get('mrp.production')
        move_obj = self.pool.get('stock.move')
        
        #check if there is any MO related to manufacturing product moves picking
        production_ids = prod_obj.search(cr, uid, [('picking_id','in',ids),('state','not in',['draft','done','cancel'])])
        if production_ids:
            for prod in prod_obj.browse(cr, uid, production_ids):
                if prod.bom_id and prod.bom_id.type == 'automatic':
                    if prod.move_lines:
                        for move_id in prod.move_lines:
                            move_obj.action_consume(cr, uid, [move_id.id],
                                 move_id.product_qty, move_id.location_id.id,
                                 context=context)
                    #TODO:
                    #technically we don't need to call the workflow for mrp.production button_produce as its been automatically called in mrp/stock.py -->action_consume.
                    #When I manually click on stock_move.action_consume, the MO state changes to in_production but while calling from here, it doesnt change the state. Wierd behaviour!
                    if prod.state == 'confirmed':
                        prod_obj.force_production(cr, uid, [prod.id])
                    wf_service.trg_validate(uid, 'mrp.production', prod.id, 'button_produce', cr)
                    
        #Change the MO state to done when the incoming shipment for finished product is changed to done!
        #check if there is any MO related to finished product moves picking
        production_ids = prod_obj.search(cr, uid, [('incoming_shipment_id','in',ids),('state','not in',['draft','done','cancel'])])
        if production_ids:
            for prod in prod_obj.browse(cr, uid, production_ids):
                if prod.bom_id and prod.bom_id.type == 'automatic':
                        #TODO: calls the function but doesn't write the state to database. Something wrong b'coz it returns a false value
                        r = wf_service.trg_validate(uid, 'mrp.production', prod.id, 'button_produce_done', cr)
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