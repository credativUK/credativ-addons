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
                    LEFT OUTER JOIN purchase_order poe ON poe.origin = po.name
                    WHERE po.warehouse_id IN %s
                    AND sp.state = 'cancel'
                    AND po.state = 'cancel'
                    AND poe.id IS NULL
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
            del_po_ids = self.get_deleted_pos(cr, uid, [warehouse.id,], warehouse.referential_id.id, context=context)
            # Find POs to create/update/delete
            new_po_ids = self.get_exportable_pos(cr, uid, [warehouse.id,], warehouse.referential_id.id, context=context)
            po_ids = list(set(del_po_ids + new_po_ids))
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
            po_import, fn = self.pool.get('external.referential')._import(cr, uid, warehouse.mapping_purchase_orders_import_id, context=context)
            if not fn:
                continue
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
            
            _cr = pooler.get_db(cr.dbname).cursor()
            try:
                po_obj.wms_import_moves(_cr, uid, [], imported_sm, context=context) # This can tollerate importing the same file twice, it will not process anything on the second pass since SMs are in the wrong state
                _cr.commit()
                if fn:
                    conn = self.pool.get('external.referential').external_connection(_cr, uid, warehouse.mapping_purchase_orders_import_id.referential_id.id, DEBUG, context=context)
                    fpath, fname = os.path.split(fn)
                    remote_csv_fn_rn = os.path.join(fpath, 'Archives', fname)
                    _logger.info("Archiving imported advice file %s as %s" % (fn, remote_csv_fn_rn))
                    conn.rename_file(fn, remote_csv_fn_rn, context=context)
                    conn.finalize_rename(context=context)
                    _cr.commit()
            except:
                _cr.rollback()
                raise
            finally:
                _cr.close()
            
        return True

    def get_exportable_dispatches(self, cr, uid, ids, referential_id, context=None):
        if context == None:
            context = {}
        if not ids:
            return []
        
        params = [('state', 'in', ('confirmed', 'assigned')), ('warehouse_id', 'in', ids),]
        params.extend(context.get('search_export_dispatch_orders', []))
        
        sd_ids = self.pool.get('stock.dispatch').search(cr, uid, params, context=context)
        return sd_ids

    def export_dispatch_orders(self, cr, uid, ids, context=None):
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

    def import_dispatch_receipts(self, cr, uid, ids, context=None):
        if context == None:
            context = {}
        if not isinstance(ids, list):
            ids = [ids]
        sd_obj = self.pool.get('stock.dispatch')
        sm_obj = self.pool.get('stock.move')
        
        for warehouse in self.browse(cr, uid, ids):
            if not warehouse.referential_id or not warehouse.mapping_dispatch_orders_import_id:
                continue
            
            # Find SD files to import
            sd_import, fn = self.pool.get('external.referential')._import(cr, uid, warehouse.mapping_dispatch_orders_import_id, context=context)
            if not fn:
                continue
            sm_lines = []
            [sm_lines.extend(x) for x in sd_import]
            
            imported_sm = {}
            # Map each stock move to the corresponding id through ir_model_data
            for sm_line in sm_lines:
                external_name = "%s_%s" % (sm_line['ref'], sm_line['lineref'])
                erp_id = sm_obj.extid_to_oeid(cr, uid, external_name, warehouse.referential_id.id, context=context)
                if erp_id:
                    imported_sm[erp_id] = sm_line
                    _logger.info('Imported Dispatch stock move %s mapped to OpenERP ID %d' % (external_name, erp_id))
                else:
                    _logger.warn('Imported Dispatch stock move %s does not exist in OpenERP' % (external_name,))
            
            _cr = pooler.get_db(cr.dbname).cursor()
            try:
                sd_obj.wms_import_moves(cr, uid, [], imported_sm, context=context) # This can tollerate importing the same file twice, it will not process anything on the second pass since SMs are in the wrong state
                _cr.commit()
                if fn:
                    conn = self.pool.get('external.referential').external_connection(_cr, uid, warehouse.mapping_dispatch_orders_import_id.referential_id.id, DEBUG, context=context)
                    fpath, fname = os.path.split(fn)
                    remote_csv_fn_rn = os.path.join(fpath, 'Archives', fname)
                    _logger.info("Archiving imported advice file %s as %s" % (fn, remote_csv_fn_rn))
                    conn.rename_file(fn, remote_csv_fn_rn, context=context)
                    conn.finalize_rename(context=context)
                    _cr.commit()
            except:
                _cr.rollback()
                raise
            finally:
                _cr.close()
        return True

    def run_export_purchase_orders_scheduler(self, cr, uid, context=None):
        warehouse_ids = self.search(cr, uid, [], context=context)
        for warehouse in self.browse(cr, uid, warehouse_ids, context=context):
            if warehouse.referential_id:
                warehouse.export_purchase_orders(context=context)
        return True

    def run_export_dispatch_orders_scheduler(self, cr, uid, context=None):
        warehouse_ids = self.search(cr, uid, [], context=context)
        for warehouse in self.browse(cr, uid, warehouse_ids, context=context):
            if warehouse.referential_id:
                warehouse.export_dispatch_orders(context=context)
        return True

    def run_import_purchase_order_receipts_scheduler(self, cr, uid, context=None):
        warehouse_ids = self.search(cr, uid, [], context=context)
        for warehouse in self.browse(cr, uid, warehouse_ids, context=context):
            if warehouse.referential_id:
                warehouse.import_purchase_order_receipts(context=context)
        return True

    def run_import_dispatch_receipts_scheduler(self, cr, uid, context=None):
        warehouse_ids = self.search(cr, uid, [], context=context)
        for warehouse in self.browse(cr, uid, warehouse_ids, context=context):
            if warehouse.referential_id:
                warehouse.import_dispatch_receipts(context=context)
        return True

stock_warehouse()
