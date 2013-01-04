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
        import ipdb; ipdb.set_trace()
        if context == None:
            context = {}
        po = self.browse(cr, uid, id, context=context)
        
        picking_ids = self.pool.get('stock.picking').search(cr, uid, [('purchase_id', '=', po.id)], context=context)
        move_ids = self.pool.get('stock.move').search(cr, uid, [('picking_id', 'in', picking_ids)], context=context)
        
        if 'remote_csv_fn_sub' not in context:
            context['remote_csv_fn_sub'] = (po.name.split('-edit')[0], datetime.now().strftime('%Y-%m-%dT%H:%M:%S'))
        
        self.pool.get('external.referential')._export(cr, uid, po.warehouse_id.referential_id.id, 'stock.move', move_ids, context=context)
        
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
                        last_exported_times = data_obj.read(cr, uid, rec_check_ids[0], ['write_date', 'create_date'])
                        last_exported_time = last_exported_times.get('write_date', False) or last_exported_times.get('create_date', False)
                        this_record_times = self.read(cr, uid, po.id, ['write_date', 'create_date'])
                        last_updated_time = this_record_times.get('write_date', False) or this_record_times.get('create_date', False)
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

class stock_warehouse(osv.osv):
    _inherit = "stock.warehouse"

    _columns = {
        'referential_id': fields.many2one('external.referential', string='External Referential'),
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
        
        # TODO: Add functionality for deleting cancelled POs
        
        return True

stock_warehouse()
