# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution   
#    Copyright (C) 2012 credativ ltd (<http://www.credativ.co.uk>). All Rights Reserved
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from osv import osv, fields
from tools.translate import _
import netsvc
import logging
from datetime import datetime
import pooler
import os
DEBUG = True

_logger = logging.getLogger(__name__)

class purchase_order(osv.osv):
    _inherit = "purchase.order"

    def _prepare_external_id_vals(self, cr, uid, res_id, ext_id, external_referential_id, context=None):
        ir_model_data_vals = super(purchase_order, self)._prepare_external_id_vals(cr, uid, res_id, ext_id, external_referential_id, context=context)
        if context.get('external_log_id'):
            ir_model_data_vals.update({'external_log_id': context['external_log_id']})
        return ir_model_data_vals

    _columns = {
        'warehouse_id': fields.many2one('stock.warehouse', 'Warehouse', required=True, states={'confirmed':[('readonly',True)], 'approved':[('readonly',True)],'done':[('readonly',True)]}),
    }

    def wms_export_one(self, cr, uid, ids, context=None):
        if context == None:
            context = {}
        
        ctx = context.copy()
        
        move_pool = self.pool.get('stock.move')
        data_pool = self.pool.get('ir.model.data')
        extref_pool = self.pool.get('external.referential')
        extlog_pool = self.pool.get('external.log')
        pos = self.browse(cr, uid, ids, context=ctx) # po[0] is our current PO, po[1:] are our edits which are now cancelled (if any)
        po = pos[0]
        
        external_log_id = extlog_pool.start_transfer(cr, uid, [], po.warehouse_id.referential_id.id, 'purchase.order', 'PO_%s' % (po.name.split('-edit')[0],), context=context)
        ctx['external_log_id'] = external_log_id
        
        ir_model_data_rec = {
            'name': 'purchase_order/' + po.name.split('-edit')[0],
            'model': 'purchase.order',
            'external_log_id': ctx.get('external_log_id', None),
            'res_id': po.id,
            'external_referential_id': po.warehouse_id.referential_id.id,
            'module': 'pendref/' + po.warehouse_id.referential_id.name}
        data_pool.create(cr, uid, ir_model_data_rec, context=ctx)
        
        picking_ids = self.pool.get('stock.picking').search(cr, uid, [('purchase_id', 'in', [x.id for x in pos])], context=ctx)
        all_move_ids = self.pool.get('stock.move').search(cr, uid, [('picking_id', 'in', picking_ids)], context=ctx)
        
        wms_sm_sequence = {}
        wms_sm_mode = {}
        move_ids = []
        
        for move in move_pool.browse(cr, uid, all_move_ids, context=ctx):
            
            if move.picking_id.type != 'in':
                continue # We only want stock from 'in' pickings
            
            rec_check_ids = data_pool.search(cr, uid, [('model', '=', 'stock.move'), ('res_id', '=', move.id), ('module', 'ilike', 'extref'), ('external_referential_id', '=', po.warehouse_id.referential_id.id)])
            
            if not (move.state == 'assigned' or (move.state == 'cancel' and rec_check_ids)):
                continue # We only want exisintg or new ongoing moves, or moves which the external WMS knows about and need deleting
            
            if rec_check_ids:
                rec_check = data_pool.browse(cr, uid, rec_check_ids[0], context=ctx)
                try:
                    po_name, sm_seq = rec_check.name.split('/')[1].split('_')
                    sm_seq = int(sm_seq)
                    assert po_name == po.name.split('-edit')[0]
                except Exception, e:
                    # Something is wrong with this referential, delete it and create a new one
                    data_pool.unlink(cr, uid, rec_check_ids[0], context=ctx)
                    rec_check_ids = []
                else:
                    wms_sm_sequence[move.id] = sm_seq
                    if move.state == 'cancel':
                        wms_sm_mode[move.id] = 'delete'
                    else:
                        wms_sm_mode[move.id] = 'update'
                    move_ids.append(move.id)
                    rec_check = data_pool.browse(cr, uid, rec_check_ids[0], context=ctx)
                    ir_model_data_rec = {
                        'name': rec_check.name,
                        'model': rec_check.model,
                        'external_log_id': ctx.get('external_log_id', None),
                        'res_id': rec_check.res_id,
                        'external_referential_id': rec_check.external_referential_id.id,
                        'module': 'pendref/' + rec_check.external_referential_id.name}
                    data_pool.create(cr, uid, ir_model_data_rec)
            
            if not rec_check_ids:
                # Find the next number in the sequence and create the ir_model_data entry for it
                cr.execute("""SELECT
                            MAX(COALESCE(SUBSTRING(name from 'stock_move/%s_([0-9]*)'), '0')::INTEGER) + 1
                            FROM ir_model_data imd
                            WHERE external_referential_id = %s
                            AND model = 'stock.move'
                            AND (module ilike 'extref%%'
                            OR module ilike 'pendref%%')""" % (po.name.split('-edit')[0], po.warehouse_id.referential_id.id,))
                number = cr.fetchall()
                if number and number[0][0]:
                    sm_seq = number[0][0]
                else:
                    sm_seq = 1
                
                ir_model_data_rec = {
                    'name': "stock_move/%s_%d" % (po.name.split('-edit')[0], sm_seq),
                    'model': 'stock.move',
                    'external_log_id': ctx.get('external_log_id', None),
                    'res_id': move.id,
                    'external_referential_id': po.warehouse_id.referential_id.id,
                    'module': 'pendref/' + po.warehouse_id.referential_id.name}
                data_pool.create(cr, uid, ir_model_data_rec)
                
                wms_sm_sequence[move.id] = sm_seq
                wms_sm_mode[move.id] = 'create'
                move_ids.append(move.id)
        
        if move_ids:
            ctx2 = ctx.copy()
            ctx2.update({'wms_sm_sequence': wms_sm_sequence, 'wms_sm_mode': wms_sm_mode, 'name': po.name.split('-edit')[0]})
            if po.warehouse_id.mapping_purchase_orders_id:
                ctx2.update({'external_mapping_ids': [po.warehouse_id.mapping_purchase_orders_id.id,]})
            extref_pool._export(cr, uid, po.warehouse_id.referential_id.id, 'stock.move', move_ids, context=ctx2)
        else:
            raise # If we have no move_ids to export we need to abort the transaction so we do not get stuck waiting for an import
        
        extlog_pool.end_transfer(cr, uid, external_log_id, context=context)
        
        return

    def wms_export_orders(self, cr, uid, ids, referential_id, context=None):
        if context == None:
            context = {}
        data_pool = self.pool.get('ir.model.data')
        
        pos = self.browse(cr, uid, ids)
        ctx = context.copy()
        if pos and pos[0].warehouse_id.mapping_purchase_orders_id:
            ctx.update({'external_mapping_ids': [pos[0].warehouse_id.mapping_purchase_orders_id.id,]})

        for po in pos:
            try:
                _cr = pooler.get_db(cr.dbname).cursor()
                if not po.warehouse_id or not po.warehouse_id.referential_id:
                    # FIXME: We should log a warning here
                    continue
                
                ext_id = self.oeid_to_extid(_cr, uid, po.id, po.warehouse_id.referential_id.id, context=context)
                
                po_edit = po # Functionality to support edited POs from the order_edit module
                while not ext_id and '-edit' in po_edit.name and po_edit.origin:
                    po_edit_id = self.search(_cr, uid, [('name', '=', po_edit.origin)], context=context)
                    if not po_edit_id:
                        break
                    po_edit = self.browse(_cr, uid, po_edit_id, context=context)
                    if not po_edit or not po_edit[0] or not po_edit[0].warehouse_id or not po_edit[0].warehouse_id.referential_id:
                        break
                    po_edit = po_edit[0]
                    ext_id = self.oeid_to_extid(_cr, uid, po_edit.id, po.warehouse_id.referential_id.id, context=context)
                
                if not ext_id: # We have not already been exported, export as new
                    self.wms_export_one(_cr, uid, [po.id,], context=context)
                else: # Exported already, check if we have been edited
                    rec_check_ids = data_pool.search(_cr, uid, [('model', '=', self._name), ('res_id', '=', po.id), ('module', 'ilike', 'extref'), ('external_referential_id', '=', po.warehouse_id.referential_id.id)])
                    if rec_check_ids:
                        _cr.execute("""select coalesce(write_date, create_date) from ir_model_data where id = %s""", (rec_check_ids[0],))
                        last_exported_time = _cr.fetchall()[0][0] or False
                        _cr.execute("""select coalesce(write_date, create_date) from purchase_order where id = %s""", (po.id,))
                        last_updated_time = _cr.fetchall()[0][0] or False
                        if last_updated_time < last_exported_time: # Do not export again if it does not need to be
                            continue
                    else:
                        rec_check_ids = data_pool.search(_cr, uid, [('model', '=', self._name), ('res_id', '=', po_edit.id), ('module', 'ilike', 'extref'), ('external_referential_id', '=', po.warehouse_id.referential_id.id)])
                    
                    if po_edit.id != po.id:
                        self.wms_export_one(_cr, uid, [po.id, po_edit.id,], context=context)
                    else:
                        self.wms_export_one(_cr, uid, [po.id,], context=context)
            except osv.except_osv, e:
                if e.value == u'Will not export while incomplete transfers exist':
                    _cr.rollback()
                else:
                    raise
            except:
                _cr.rollback()
                raise
            else:
                _cr.commit()
            finally:
                _cr.close()
        
        return True
    
    def wms_import_moves(self, cr, uid, ids, move_lines, context=None):
        sm_obj = self.pool.get('stock.move')
        pick_obj = self.pool.get('stock.picking')
        
        stock_moves = sm_obj.browse(cr, uid, move_lines.keys(), context=context)
        picking_dict = {}
        
        add_moves = {}
        add_moves['less'] = []
        add_moves['more'] = []
        
        for stock_move in stock_moves:
            picking_dict.setdefault(stock_move.picking_id, []).append(stock_move)
        
        for picking, moves in picking_dict.iteritems():
            for move in picking.move_lines:
                lot_missing_id = (picking.purchase_id.warehouse_id.lot_missing_id and picking.purchase_id.warehouse_id.lot_missing_id.id
                                                                                  or move.product_id.product_tmpl_id.property_stock_inventory.id)
                rqty = float(move_lines.get(move.id, {}).get('qty', 0.0))
                if move.state not in ('assigned'):
                    _logger.warn('Stock move %d in unexpected state %s, skipping' % (move.id, move.state,))
                    continue
                if move.product_qty == rqty: # Exact amount received
                    sm_obj.action_done(cr, uid, [move.id], context=context)
                elif move.product_qty < rqty: # Too much received
                    new_data = {
                            'product_qty':  rqty - move.product_qty,
                            'product_uos_qty':  rqty - move.product_qty,
                            'location_id': lot_missing_id,
                        }
                    new_sm = sm_obj.copy(cr, uid, move.id, new_data, context=context)
                    sm_obj.action_done(cr, uid, [move.id, new_sm], context=context)
                    add_moves['more'].append(new_sm)
                else: # Too little received
                    new_data = {
                            'product_qty': move.product_qty - rqty,
                            'product_uos_qty': move.product_qty - rqty,
                            'location_dest_id': lot_missing_id,
                        }
                    new_sm = sm_obj.copy(cr, uid, move.id, new_data, context=context)
                    sm_obj.action_done(cr, uid, [new_sm], context=context)
                    add_moves['less'].append(new_sm)
                    if rqty:
                        sm_obj.write(cr, uid, [move.id], {'product_qty': rqty, 'product_uos_qty': rqty}, context=context)
                        sm_obj.action_done(cr, uid, [move.id], context=context)
                    else: # None received
                        sm_obj.write(cr, uid, [move.id], {'product_qty': 0, 'product_uos_qty': 0}, context=context)
                        sm_obj.action_cancel(cr, uid, [move.id], context=context)
            
            picking = pick_obj.browse(cr, uid, picking.id, context=context)
            if not all([x.state in ('done', 'cancel') for x in picking.move_lines]):
                _logger.error('Not all stock moves in picking %d are in the expected states' % (picking.id,))
            else:
                pick_obj.action_done(cr, uid, [picking.id], context=context)
        return add_moves
    
purchase_order()
