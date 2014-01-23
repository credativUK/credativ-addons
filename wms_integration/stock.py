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
import pooler
import os
DEBUG = True
import csv
import base64
from tempfile import TemporaryFile

_logger = logging.getLogger(__name__)


def enc(s):
    if isinstance(s, unicode):
        return s.encode('utf8')
    return s


def get_csv_format(columns_header, lines_to_export):
    outfile = TemporaryFile('w+')
    writer = csv.writer(outfile, quotechar='"', delimiter=',')
    writer.writerow([enc(x[0]) for x in columns_header])
    for line in lines_to_export:
        writer.writerow([enc(x) for x in line])
    outfile.seek(0)
    file_to_export = base64.encodestring(outfile.read())
    outfile.close()
    return file_to_export


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
        'mapping_stock_image_import_id': fields.many2one('external.mapping', string='Stock Image'),
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
            _cr = pooler.get_db(cr.dbname).cursor()
            try:
                po_import, fn = self.pool.get('external.referential')._import(_cr, uid, warehouse.mapping_purchase_orders_import_id, context=context)
            except:
                _cr.rollback()
                raise
            finally:
                _cr.close()
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
            _cr = pooler.get_db(cr.dbname).cursor()
            try:
                sd_import, fn = self.pool.get('external.referential')._import(_cr, uid, warehouse.mapping_dispatch_orders_import_id, context=context)
            except:
                _cr.rollback()
                raise
            finally:
                _cr.close()
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

    def save_report_in_attachment(self, cr, uid, ids, file_exported, filename, context):
        """
        Version the reports
        """
        vals = {'report_config_id': ids[0],
                'name': filename,
                'res_model': 'report.config',
                'datas': file_exported,
                'datas_fname': filename,
                'res_id': False}
        return self.pool.get('ir.attachment').create(cr, uid, vals, context)

    def import_stock_image(self, cr, uid, ids, context=None):
        if context == None:
            context = {}
        if not isinstance(ids, list):
            ids = [ids]
        product_obj = self.pool.get('product.product')
        msg_obj = self.pool.get('mail.compose.message')
        data_obj = self.pool.get('ir.model.data')
        for warehouse in self.browse(cr, uid, ids):
            if not warehouse.referential_id or not warehouse.mapping_purchase_orders_import_id:
                continue
            
            _cr = pooler.get_db(cr.dbname).cursor()
            try:
                stock_image_import, fn = self.pool.get('external.referential')._import(_cr, uid, warehouse.mapping_stock_image_import_id, context=context)
            except:
                _cr.rollback()
                raise
            finally:
                _cr.close()
            if not fn:
                continue
            ext_list_dict = stock_image_import[0]
            ext_dict = dict([(x['sku'], x) for x in ext_list_dict])
            ext_sku_list = ext_dict.keys()
            cr.execute("select p.default_code from mrp_bom b left join product_product p on b.product_id=p.id where b.bom_id is null")
            bom_list = [x[0] for x in cr.fetchall()]
            p_ids = product_obj.search(cr, uid, [], context=context)
            internal_dict = dict([(x['default_code'], x) for x in product_obj.read(cr, uid, p_ids, ['default_code', 'qty_available'], context)])
            internal_sku_list = internal_dict.keys()
            message = ""
            list_to_check = [x for x in internal_sku_list if x in ext_sku_list and x not in bom_list]
            lines_to_export = []
            for product in list_to_check:
                ext_qty = ext_dict[product]['qty'].strip()
                internal_qty = internal_dict[product]['qty_available']
                if not ext_qty:
                    ext_qty = 0
                if not internal_qty:
                    internal_qty = 0
                diff = int(ext_qty) - int(internal_qty)
                if diff != 0:
                    message += "%s: %s \n" % (product, diff)
                    lines_to_export.append([product, diff])
            # Create csv file
            file_exported = get_csv_format([ (_('SKU'), 'string'), (_('Difference'), 'number')], lines_to_export)
            # Create attachment
            attachment_id = False
            if file_exported:
                attachment_id = self.save_report_in_attachment(cr, uid, ids, file_exported, "Stock_discrepancies.csv", context)
            # Create email based on the template "Stock Image Report Mail"
            template_id = data_obj.get_object_reference(cr, uid, 'wms_integration', 'email_template_stock_image')[1]
            onchange = msg_obj.on_change_template(cr, uid, [], True, template_id)
            vals = onchange.get('value')
            attachment_id and vals.update({'attachment_ids': [(6, 0, [attachment_id])]})
            msg_id = msg_obj.create(cr, uid, vals)
            # Send email
            msg_obj.send_mail(cr, uid, [msg_id], context)
            # Delete attachment
            self.pool.get('ir.attachment').unlink(cr, uid, [attachment_id], context)
            _cr = pooler.get_db(cr.dbname).cursor()
            try:
                if fn:
                    conn = self.pool.get('external.referential').external_connection(_cr, uid, warehouse.mapping_stock_image_import_id.referential_id.id, DEBUG, context=context)
                    fpath, fname = os.path.split(fn)
                    remote_csv_fn_rn = os.path.join(fpath, 'Archives', fname)
                    _logger.info("Archiving imported STOCK IMAGE file %s as %s" % (fn, remote_csv_fn_rn))
                    conn.rename_file(fn, remote_csv_fn_rn, context=context)
                    conn.finalize_rename(context=context)
                    _cr.commit()
            except:
                _cr.rollback()
                raise
            finally:
                _cr.close()
        return True

    def run_import_stock_image_scheduler(self, cr, uid, context=None):
        warehouse_ids = self.search(cr, uid, [], context=context)
        for warehouse in self.browse(cr, uid, warehouse_ids, context=context):
            if warehouse.referential_id:
                _logger.info("Running Stock Image comparison scheduler for Warehouse %d" % (warehouse.id))
                warehouse.import_stock_image(context=context)
        return True

    def run_export_purchase_orders_scheduler(self, cr, uid, context=None):
        warehouse_ids = self.search(cr, uid, [], context=context)
        for warehouse in self.browse(cr, uid, warehouse_ids, context=context):
            if warehouse.referential_id:
                _logger.info("Running PO export scheduler for Warehouse %d" % (warehouse.id))
                warehouse.export_purchase_orders(context=context)
        return True

    def run_export_dispatch_orders_scheduler(self, cr, uid, context=None):
        warehouse_ids = self.search(cr, uid, [], context=context)
        for warehouse in self.browse(cr, uid, warehouse_ids, context=context):
            if warehouse.referential_id:
                _logger.info("Running Dispatch export scheduler for Warehouse %d" % (warehouse.id))
                warehouse.export_dispatch_orders(context=context)
        return True

    def run_import_purchase_order_receipts_scheduler(self, cr, uid, context=None):
        warehouse_ids = self.search(cr, uid, [], context=context)
        for warehouse in self.browse(cr, uid, warehouse_ids, context=context):
            if warehouse.referential_id:
                _logger.info("Running PO import scheduler for Warehouse %d" % (warehouse.id))
                warehouse.import_purchase_order_receipts(context=context)
        return True

    def run_import_dispatch_receipts_scheduler(self, cr, uid, context=None):
        warehouse_ids = self.search(cr, uid, [], context=context)
        for warehouse in self.browse(cr, uid, warehouse_ids, context=context):
            if warehouse.referential_id:
                _logger.info("Running Dispatch import scheduler for Warehouse %d" % (warehouse.id))
                warehouse.import_dispatch_receipts(context=context)
        return True

stock_warehouse()
