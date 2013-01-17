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

        external_log_id = self.pool.get('external.log').start_transfer(cr, uid, [], referential_id, 'stock.move', context=context)
        #external_log = self.pool.get('external.log').browse(cr, uid, external_log_id, context=context)
        context['external_log_id'] = external_log_id

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

        self.pool.get('external.log').end_transfer(cr, uid, external_log_id, context=context)

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
            address_groups = {}
            for move in dispatch.stock_moves: # Group moves by the customer delivery address
                address_groups.setdefault(move.address_id.id, []).append(move)

            for address_id, moves in address_groups.iteritems():
                move_ids = []
                for move in moves:
                    rec_check_ids = data_pool.search(cr, uid, [('model', '=', 'stock.move'), ('res_id', '=', move.id), ('module', 'ilike', 'extref'), ('external_referential_id', '=', dispatch.warehouse_id.referential_id.id)])
                    
                    if rec_check_ids:
                        rec_checks = data_pool.browse(cr, uid, rec_check_ids, context=context)
                        rec_check_ids = []
                        for rec_check in rec_checks:
                            try:
                                dispatch_name, address_name, sm_seq = rec_check.name.split('/')[1].split('_')
                                if dispatch_name == dispatch.name and address_name == '%d' % (address_id,):
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
                                    MAX(COALESCE(SUBSTRING(name from 'stock_move/%s_%d_([0-9]*)'), '0')::INTEGER) + 1
                                    FROM ir_model_data imd
                                    WHERE external_referential_id = %s
                                    AND model = 'stock.move'
                                    AND module ilike 'extref%%'""" % (dispatch.name, address_id, dispatch.warehouse_id.referential_id.id,))
                        number = cr.fetchall()
                        if number and number[0][0]:
                            sm_seq = number[0][0]
                        else:
                            sm_seq = 1
                        
                        move_pool.create_external_id_vals(cr, uid, move.id, "%s_%d_%d" % (dispatch.name, address_id, sm_seq), dispatch.warehouse_id.referential_id.id, context=context)
                        
                        wms_sm_sequence[move.id] = sm_seq
                        move_ids.append(move.id)
                final_move_ids.extend(move_ids)
        
        if final_move_ids:
            ctx = context.copy()
            ctx.update({'wms_sm_sequence': wms_sm_sequence})
            if dispatch.warehouse_id.mapping_dispatch_orders_id:
                ctx.update({'external_mapping_ids': [dispatch.warehouse_id.mapping_dispatch_orders_id.id,]})

            external_log_id = self.pool.get('external.log').start_transfer(cr, uid, [], dispatch.warehouse_id.referential_id.id, 'stock.move', context=context)
            #external_log = self.pool.get('external.log').browse(cr, uid, external_log_id, context=context)
            ctx['external_log_id'] = external_log_id

            self.pool.get('external.referential')._export(cr, uid, dispatch.warehouse_id.referential_id.id, 'stock.move', final_move_ids, context=ctx)

            self.pool.get('external.log').end_transfer(cr, uid, external_log_id, context=context)
        
        return
    
    def wms_export_orders(self, cr, uid, ids, referential_id, context=None):
        if context == None:
            context = {}

        export_dispatch_ids = []
        
        for dispatch in self.browse(cr, uid, ids):
            if not dispatch.warehouse_id or not dispatch.warehouse_id.referential_id:
                continue
            
            try:
                ext_id = self.oeid_to_extid(cr, uid, dispatch.id, dispatch.warehouse_id.referential_id.id, context=context)
                if not ext_id: # We should only export new dispatches
                    self.create_external_id_vals(cr, uid, dispatch.id, dispatch.id, dispatch.warehouse_id.referential_id.id, context=context)
                    export_dispatch_ids.append(dispatch.id)
                else: # Exported already, skip
                    continue
            
            except Exception, e:
                raise
                pass
        
        self.wms_export_all(cr, uid, export_dispatch_ids, context=context)
            
        return True

stock_dispatch()

class stock_warehouse(osv.osv):
    _inherit = "stock.warehouse"

    _columns = {
        'referential_id': fields.many2one('external.referential', string='External Referential'),
        'lot_missing_id': fields.many2one('stock.location', 'Missing Stock Location', domain=[('usage','<>','view')],
            help='This location is used similar to inventory loss for discrepancies for automatic Purhcase Order imports through the external WMS. If not filled Inventory Loss will be used.'),
        'mapping_purchase_orders_id': fields.many2one('external.mapping', string='Override Purchase Orders Export Mapping'),
        'mapping_dispatch_orders_id': fields.many2one('external.mapping', string='Override Dispatch Export Mapping'),
        'mapping_purchase_orders_import_id': fields.many2one('external.mapping', string='Override Purchase Orders Import Mapping'),
        'mapping_dispatch_orders_import_id': fields.many2one('external.mapping', string='Override Dispatch Import Mapping'),
    }
    _override_mappings = ['mapping_purchase_orders_id', 'mapping_dispatch_orders_id']
    
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

    def import_export_confirmations(self, cr, uid, ids, model_name, success_fun, external_log_id, context=None):
        '''
        This method implements the import of the data confirming the
        receipt of exported records.

        @model_name (str): is the name of model from which the export
        was made.

        @external_log_id (int): ID of an external_log whose child
        export records will be polled for confirmation

        @success_fun (function): is a Boolean function of two
        arguments, the exported record and the corresponding
        confirmation record; it should return True if the export of
        the record was successful, or False otherwise
        '''
        if context is None:
            context = {}
        extref_pool = self.pool.get('external.referential')

        model_pool = self.pool.get('ir.model')
        mapping_pool = self.pool.get('external.mapping')

        for warehouse in self.browse(cr, uid, ids):
            if not warehouse.referential_id:
                continue

            # get the mapping; either from one of the override
            # mappings, or from the given model
            mapping_ids = [getattr(warehouse, ovr_mapping) for ovr_mapping in self._override_mappings]
            if not mapping_ids:
                model_ids = model_pool.search(cr, uid, [('model','=',model_name)])
                if len(model_ids) > 1:
                    raise osv.except_osv(_('Integrity error'), _('Model name "%s" is ambiguous.' % (model_name,)))
                if not model_ids:
                    raise osv.except_osv(_('Data error'), _('No such model: "%s"' % (model_name,)))
                model_id = model_ids[0]
                mapping_ids = mapping_pool.search(cr, uid, [('referential_id','=',warehouse.referential_id.id),
                                                            ('model_id','=',model_id),
                                                            ('purpose','=','data')])

            if not mapping_ids:
                raise osv.except_osv(_('Configuration error'),
                                     _('No mappings found for the referential "%s" of type "%s"' %\
                                           (warehouse.referential_id.name, warehouse.referential_id.type_id.name)))

            res = {}

            for mapping in mapping_pool.browse(cr, uid, mapping_ids):
                referential = extref_pool.browse(cr, uid, warehouse.referential_id.id, context=context)
                exported_ids = referential._get_exported_ids_by_log(cr, uid, warehouse.referential_id.id, mapping.model_id.model, external_log_id, context=context)
                res[mapping.id] = extref_pool._verify_export(cr, uid, mapping, exported_ids, success_fun, context=context)

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

    def import_purchase_order_receipts(self, cr, uid, ids, context=None):
        if context == None:
            context = {}
        if not isinstance(ids, list):
            ids = [ids]
        po_obj = self.pool.get('purchase.order')
        sm_obj = self.pool.get('stock.move')
        
        for warehouse in self.browse(cr, uid, ids):
            if not warehouse.referential_id or not warehouse.mapping_purchase_orders_import_id:
                continue
            
            # Find PO files to import
            po_import = self.pool.get('external.referential')._import(cr, uid, warehouse.mapping_purchase_orders_import_id, context=context)
            sm_lines = []
            [sm_lines.extend(x) for x in po_import]
            
            imported_sm = {}
            # Map each stock move to the corresponding id through ir_model_data
            for sm_line in sm_lines:
                external_name = "%s_%s" % (sm_line['ref'], sm_line['lineref'])
                erp_id = sm_obj.extid_to_oeid(cr, uid, external_name, warehouse.referential_id.id, context=context)
                if erp_id:
                    imported_sm[erp_id] = sm_line
                    _logger.info('Imported PO stock move %s mapped to OpenERP ID %d' % (external_name, erp_id))
                else:
                    _logger.warn('Imported PO stock move %s does not exist in OpenERP' % (external_name,))
            po_obj.wms_import_moves(cr, uid, [], imported_sm, context=context)
        # TODO: Archive files after import
        return True

    def import_purchase_order_export_confirmation(self, cr, uid, ids, context=None):
        '''
        This method imports the confirmation of receipt of export data.
        '''
        if context == None:
            context = {}

        # The success_func for the verification has no data to work
        # with, so we'll just return True
        return self.import_export_confirmations(cr, uid, ids, model_name='stock.move', success_fun=lambda exp, conf: True, context=context)

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
