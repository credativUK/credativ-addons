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
import logging
from datetime import datetime

_logger = logging.getLogger(__name__)

class purchase_order(osv.osv):
    _inherit = "purchase.order"

    _columns = {
        'warehouse_id': fields.many2one('stock.warehouse', 'Warehouse', required=True, states={'confirmed':[('readonly',True)], 'approved':[('readonly',True)],'done':[('readonly',True)]}),
    }

    def wms_export_one(self, cr, uid, id, context=None):
        if context == None:
            context = {}
        move_pool = self.pool.get('stock.move')
        data_pool = self.pool.get('ir.model.data')
        po = self.browse(cr, uid, id, context=context)
        
        picking_ids = self.pool.get('stock.picking').search(cr, uid, [('purchase_id', '=', po.id)], context=context)
        all_move_ids = self.pool.get('stock.move').search(cr, uid, [('picking_id', 'in', picking_ids)], context=context)
        
        wms_sm_sequence = {}
        wms_sm_mode = {}
        move_ids = []
        
        for move in move_pool.browse(cr, uid, all_move_ids, context=context):
            
            if move.location_dest_id.id != po.warehouse_id.lot_input_id.id:
                continue # We only want stock entering the input location, ie cross-dock
            
            rec_check_ids = data_pool.search(cr, uid, [('model', '=', 'stock.move'), ('res_id', '=', move.id), ('module', 'ilike', 'extref'), ('external_referential_id', '=', po.warehouse_id.referential_id.id)])
            
            if not (move.state == 'assigned' or (move.state == 'cancel' and rec_check_ids)):
                continue # We only want exisintg or new ongoing moves, or moves which the external WMS knows about and need deleting
            
            if rec_check_ids:
                rec_check = data_pool.browse(cr, uid, rec_check_ids[0], context=context)
                try:
                    po_name, sm_seq = rec_check.name.split('/')[1].split('_')
                    assert po_name == po.name.split('-edit')[0]
                except Exception, e:
                    # Something is wrong with this referential, delete it and create a new one
                    data_pool.unlink(cr, uid, rec_check_ids[0], context=context)
                    rec_check_ids = []
                else:
                    wms_sm_sequence[move.id] = sm_seq
                    if move.state == 'cancel':
                        wms_sm_mode[move.id] = 'delete'
                    else:
                        wms_sm_mode[move.id] = 'update'
                    move_ids.append(move.id)
                    data_pool.write(cr, uid, rec_check_ids[0], {}, context=context)
            
            if not rec_check_ids:
                # Find the next number in the sequence and create the ir_model_data entry for it
                cr.execute("""SELECT
                            MAX(COALESCE(SUBSTRING(name from 'stock_move/%s_([0-9]*)'), '0')::INTEGER) + 1
                            FROM ir_model_data imd
                            WHERE external_referential_id = %s
                            AND model = 'stock.move'
                            AND module ilike 'extref%%'""" % (po.name.split('-edit')[0], po.warehouse_id.referential_id.id,))
                number = cr.fetchall()
                if number and number[0][0]:
                    sm_seq = number[0][0]
                else:
                    sm_seq = 1
                
                move_pool.create_external_id_vals(cr, uid, move.id, "%s_%d" % (po.name.split('-edit')[0], sm_seq), po.warehouse_id.referential_id.id, context=context)
                
                wms_sm_sequence[move.id] = sm_seq
                wms_sm_mode[move.id] = 'create'
                move_ids.append(move.id)
        
        if move_ids:
            ctx = context.copy()
            ctx.update({'wms_sm_sequence': wms_sm_sequence, 'wms_sm_mode': wms_sm_mode, 'name': po.name.split('-edit')[0]})
            if po.warehouse_id.mapping_purchase_orders_id:
                ctx.update({'external_mapping_ids': [po.warehouse_id.mapping_purchase_orders_id.id,]})
            self.pool.get('external.referential')._export(cr, uid, po.warehouse_id.referential_id.id, 'stock.move', move_ids, context=ctx)
        
        return

    def wms_delete_orders(self, cr, uid, ids, referential_id, context=None):
        if context == None:
            context = {}
        data_obj = self.pool.get('ir.model.data')
        
        for po in self.browse(cr, uid, ids):
            if not po.warehouse_id or not po.warehouse_id.referential_id:
                continue
            
            try:
                ext_id = self.oeid_to_extid(cr, uid, po.id, po.warehouse_id.referential_id.id, context=context)
                if not ext_id: # If we have not been exported we should not enter this function
                    continue
                
                self.wms_export_one(cr, uid, po.id, context=context)
                
                rec_check_ids = data_obj.search(cr, uid, [('model', '=', self._name), ('res_id', '=', po.id), ('module', 'ilike', 'extref'), ('external_referential_id', '=', po.warehouse_id.referential_id.id)])
                if rec_check_ids:
                    data_obj.write(cr, uid, [rec_check_ids[0],], {}, context=context)
            except Exception, e:
                pass
            
        return True
    
    def wms_export_orders(self, cr, uid, ids, referential_id, context=None):
        if context == None:
            context = {}
        data_obj = self.pool.get('ir.model.data')
        
        for po in self.browse(cr, uid, ids):
            if not po.warehouse_id or not po.warehouse_id.referential_id:
                continue
            
            try:
                ext_id = self.oeid_to_extid(cr, uid, po.id, po.warehouse_id.referential_id.id, context=context)
                
                po_edit = po # Functionality to support edited POs from the order_edit module
                while not ext_id and '-edit' in po_edit.name and po_edit.origin:
                    po_edit_id = self.search(cr, uid, [('name', '=', po_edit.origin)], context=context)
                    if not po_edit_id:
                        break
                    po_edit = self.browse(cr, uid, po_edit_id, context=context)
                    if not po_edit or not po_edit[0] or not po_edit[0].warehouse_id or not po_edit[0].warehouse_id.referential_id:
                        break
                    po_edit = po_edit[0]
                    ext_id = self.oeid_to_extid(cr, uid, po_edit.id, po.warehouse_id.referential_id.id, context=context)
                
                if not ext_id: # We have not already been exported, export as new
                    
                    self.wms_export_one(cr, uid, po.id, context=context)
                    
                    self.create_external_id_vals(cr, uid, po.id, po.id, po.warehouse_id.referential_id.id, context=context)
                else: # Exported already, check if we have been edited
                    rec_check_ids = data_obj.search(cr, uid, [('model', '=', self._name), ('res_id', '=', po.id), ('module', 'ilike', 'extref'), ('external_referential_id', '=', po.warehouse_id.referential_id.id)])
                    if rec_check_ids:
                        cr.execute("""select coalesce(write_date, create_date) from ir_model_data where id = %s""", (rec_check_ids[0],))
                        last_exported_time = cr.fetchall()[0][0] or False
                        cr.execute("""select coalesce(write_date, create_date) from purchase_order where id = %s""", (po.id,))
                        last_updated_time = cr.fetchall()[0][0] or False
                        if last_updated_time < last_exported_time: # Do not export again if it does not need to be
                            continue
                    
                    self.wms_export_one(cr, uid, po.id, context=context)
                    
                    if rec_check_ids: # Update the ir.model.data entry
                        data_obj.write(cr, uid, [rec_check_ids[0],], {}, context=context)
                    else: # Create the ir.model.data entry. This is because we got the ext_id from a previous PO through an edit and we need to create a new ir.model.data entry
                        self.create_external_id_vals(cr, uid, po.id, po.id, po.warehouse_id.referential_id.id, context=context)
            
            except Exception, e:
                raise
                pass
            
        return True
    
purchase_order()

class stock_dispatch(osv.osv):
    _inherit = "stock.dispatch"
    
    def wms_export_all(self, cr, uid, ids, context=None):
        if context == None:
            context = {}
        move_pool = self.pool.get('stock.move')
        data_pool = self.pool.get('ir.model.data')
        
        final_move_ids = []
        wms_sm_sequence = {}
        
        for dispatch in self.browse(cr, uid, ids, context=context):
            move_ids = []
            for move in dispatch.stock_moves:
                
                rec_check_ids = data_pool.search(cr, uid, [('model', '=', 'stock.move'), ('res_id', '=', move.id), ('module', 'ilike', 'extref'), ('external_referential_id', '=', dispatch.warehouse_id.referential_id.id)])
                
                if rec_check_ids:
                    rec_checks = data_pool.browse(cr, uid, rec_check_ids, context=context)
                    rec_check_ids = []
                    for rec_check in rec_checks:
                        try:
                            dispatch_name, sm_seq = rec_check.name.split('/')[1].split('_')
                            if dispatch_name == dispatch.name:
                                rec_check_ids.append(rec_check.id)
                        except Exception, e:
                            # Something is wrong with this referential, delete it and create a new one
                            data_pool.unlink(cr, uid, rec_checks.id, context=context)
                            rec_check_ids = []
                        else:
                            wms_sm_sequence[move.id] = sm_seq
                            if move.state == 'cancel' or move.dispatch_id.id != dispatch.id:
                                continue
                            move_ids.append(move.id)
                            data_pool.write(cr, uid, rec_check.id, {}, context=context)
                else:
                    if move.state == 'cancel':
                        continue
                    cr.execute("""SELECT
                                MAX(COALESCE(SUBSTRING(name from 'stock_move/%s_([0-9]*)'), '0')::INTEGER) + 1
                                FROM ir_model_data imd
                                WHERE external_referential_id = %s
                                AND model = 'stock.move'
                                AND module ilike 'extref%%'""" % (dispatch.name, dispatch.warehouse_id.referential_id.id,))
                    number = cr.fetchall()
                    if number and number[0][0]:
                        sm_seq = number[0][0]
                    else:
                        sm_seq = 1
                    
                    move_pool.create_external_id_vals(cr, uid, move.id, "%s_%d" % (dispatch.name, sm_seq), dispatch.warehouse_id.referential_id.id, context=context)
                    
                    wms_sm_sequence[move.id] = sm_seq
                    move_ids.append(move.id)
            
            final_move_ids.extend(move_ids)
            
        if final_move_ids:
            ctx = context.copy()
            ctx.update({'wms_sm_sequence': wms_sm_sequence})
            if dispatch.warehouse_id.mapping_dispatch_orders_id:
                ctx.update({'external_mapping_ids': [dispatch.warehouse_id.mapping_dispatch_orders_id.id,]})
            self.pool.get('external.referential')._export(cr, uid, dispatch.warehouse_id.referential_id.id, 'stock.move', final_move_ids, context=ctx)
        
        return
    
    def wms_export_orders(self, cr, uid, ids, referential_id, context=None):
        if context == None:
            context = {}
        data_obj = self.pool.get('ir.model.data')
        export_dispatch_id = []
        
        for dispatch in self.browse(cr, uid, ids):
            if not dispatch.warehouse_id or not dispatch.warehouse_id.referential_id:
                continue
            
            try:
                ext_id = self.oeid_to_extid(cr, uid, dispatch.id, dispatch.warehouse_id.referential_id.id, context=context)
                if not ext_id: # We should only export new dispatches
                    self.create_external_id_vals(cr, uid, dispatch.id, dispatch.id, dispatch.warehouse_id.referential_id.id, context=context)
                    export_dispatch_id.append(dispatch.id)
                else: # Exported already, skip
                    continue
            
            except Exception, e:
                raise
                pass
        
        self.wms_export_all(cr, uid, export_dispatch_id, context=context)
            
        return True

stock_dispatch()

class stock_warehouse(osv.osv):
    _inherit = "stock.warehouse"

    _columns = {
        'referential_id': fields.many2one('external.referential', string='External Referential'),
        'mapping_purchase_orders_id': fields.many2one('external.mapping', string='Override Purchase Orders Export Mapping'),
        'mapping_dispatch_orders_id': fields.many2one('external.mapping', string='Override Dispatch Export Mapping'),
    }
    
    def get_exportable_pos(self, cr, uid, ids, referential_id, context=None):
        if not ids:
            return []
        cr.execute("""SELECT po.id
                    FROM purchase_order po
                    INNER JOIN stock_picking sp ON sp.purchase_id = po.id
                    WHERE po.warehouse_id IN %s
                    AND po.state = 'approved'
                    AND sp.state = 'assigned'
                    GROUP BY po.id""", (tuple(ids,),))
        po_ids = cr.fetchall()
        po_ids = self.pool.get('purchase.order').search(cr, uid, [('id', 'in', [x[0] for x in po_ids]),], context=context)
        return po_ids

    def get_deleted_pos(self, cr, uid, ids, referential_id, context=None):
        if not ids:
            return []
        cr.execute("""SELECT po.id
                    FROM purchase_order po
                    INNER JOIN stock_picking sp ON sp.purchase_id = po.id
                    LEFT OUTER JOIN ir_model_data imd ON imd.model = 'purchase.order'
                        AND imd.res_id = po.id
                        AND imd.external_referential_id = %s
                    WHERE po.warehouse_id IN %s
                    AND sp.state = 'cancel'
                    AND po.state = 'cancel'
                    AND COALESCE(imd.write_date, imd.create_date) < COALESCE(po.write_date, po.create_date)
                    GROUP BY po.id""", (referential_id, tuple(ids,),))
        po_ids = cr.fetchall()
        po_ids = self.pool.get('purchase.order').search(cr, uid, [('id', 'in', [x[0] for x in po_ids]),], context=context)
        return po_ids

    def import_export_confirmations(self, cr, uid, ids, model_name, success_fun, context=None):
        '''
        This method implements the import of the data confirming the
        receipt of exported records.

        @model_name (str): is the name of model from which the export
        was made.

        @success_fun (function): is a Boolean function of two
        arguments, the exported record and the corresponding
        confirmation record; it should return True if the export of
        the record was successful, or False otherwise
        '''
        if context is None:
            context = {}
        extref_obj = self.pool.get('external.referential')

        for warehouse in self.browse(cr, uid, ids):
            if not warehouse.referential_id:
                continue

            mapping_obj = self.pool.get('external.mapping')
            mapping_ids = mapping_obj.search(cr, uid, [('referential_id','=',warehouse.referential_id.id),('model_id','=',model_name)])
            if not mapping_ids:
                raise osv.except_osv(_('Configuration error'), _('No mappings found for the referential "%s" of type "%s"' % (warehouse.referential_id.name, warehouse.referential_id.type_id.name)))

            res = {}

            for mapping in mapping_obj.browse(cr, uid, mapping_ids):
                exported_ids = extref_obj._get_last_exported_ids(cr, uid, warehouse.referential_id.id, mapping.model_id.name, context=context)
                res[mapping.id] = extref_obj._verify_export(cr, uid, mapping, exported_ids, success_fun, context=context)

        return res

    def export_purchase_orders(self, cr, uid, ids, context=None):
        if context == None:
            context = {}
        if not isinstance(ids, list):
            ids = [ids]
        po_obj = self.pool.get('purchase.order')
        
        for warehouse in self.browse(cr, uid, ids):
            if not warehouse.referential_id:
                continue
            # Find POs to delete
            po_ids = self.get_deleted_pos(cr, uid, [warehouse.id,], warehouse.referential_id.id, context=context)
            if po_ids:
                po_obj.wms_delete_orders(cr, uid, po_ids, warehouse.referential_id.id, context=context)

            # Find POs to create/update
            po_ids = self.get_exportable_pos(cr, uid, [warehouse.id,], warehouse.referential_id.id, context=context)
            if po_ids:
                po_obj.wms_export_orders(cr, uid, po_ids, warehouse.referential_id.id, context=context)
        
        return True

    def import_purchase_order_export_confirmation(self, cr, uid, ids, context=None):
        '''
        This method imports the confirmation of receipt of export data.
        '''
        if context == None:
            context = {}

        # The success_func for the verification has no data to work
        # with, so we'll just return True
        return self.import_export_confirmations(cr, uid, ids, model_name='purchase.order', success_fun=lambda exp, conf: True, context=context)

    def import_purchase_order_receipts(self, cr, uid, ids, context=None):
        '''
        This method imports the data confirming the receipt of
        purchase order goods into the warehouse.
        '''
        pass

    def get_exportable_dispatches(self, cr, uid, ids, referential_id, context=None):
        if not ids:
            return []
        sd_ids = self.pool.get('stock.dispatch').search(cr, uid, [('state', 'in', ('confirmed', 'assigned')), ('warehouse_id', 'in', ids),], context=context)
        return sd_ids

    def export_dispatch_orders(self, cr, uid, ids, context=None):
        # TODO: We need to find what dispatches to export based on time, ie Cross-Dock only, Inventory only
        if context == None:
            context = {}
        if not isinstance(ids, list):
            ids = [ids]
        dispatch_obj = self.pool.get('stock.dispatch')
        
        for warehouse in self.browse(cr, uid, ids):
            if not warehouse.referential_id:
                continue
            # Find dispatches to create
            dispatch_ids = self.get_exportable_dispatches(cr, uid, [warehouse.id,], warehouse.referential_id.id, context=context)
            if dispatch_ids:
                dispatch_obj.wms_export_orders(cr, uid, dispatch_ids, warehouse.referential_id.id, context=context)
        
        return True


stock_warehouse()
