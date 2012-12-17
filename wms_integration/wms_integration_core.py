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
import wms_integration_osv

## TODO Decide whether ER_CSVFTP should be a separate addon or just a
## module in this addon
from external_referential_csvftp import Connection

import re
import logging

_logger = logging.getLogger(__name__)
DEBUG = True

class external_mapping(osv.osv):
    _inherit = 'external.mapping'

    def get_column_headers(self, cr, uid, ids, context=None):
        if not isinstance(ids, list):
            ids = [ids]

        res = []
        referential = self.browse(cr, uid, ids[0], context=context)
        line_ids = self.pool.get('external.mapping.lines').search(cr, uid, [('referential_id','=',referential.referential_id)])
        for line in self.pool.get('external.mapping.lines').browse(cr, uid, line_ids):
            res.append(line.external_field)

        return res

    _columns = {
        # TODO We need to store the FTP path to the confirmation CSV
        # in a way that relates it to the export. But should this be
        # in the mapping? Or in the referential? The referential
        # contains the export FTP path, but in fact this might be
        # wrong anyway
        'confirmation_referential': fields.many2one('external.referential', 'Confirmation for ')
        }

external_mapping()

class external_referential(wms_integration_osv.wms_integration_osv):
    _inherit = 'external.referential'

    _columns = {
        'active': fields.boolean('Active'),
        'last_exported_products_time': fields.datetime('Last time products exported'),
        'last_exported_purchase_orders_time': fields.datetime('Last time purchase orders exported'),
        'last_exported_sale_orders_time': fields.datetime('Last time sale orders exported'),
        'last_exported_dispatches_time': fields.datetime('Last time dispatches exported')
        }

    _defaults = {
        'active': lambda *a: 1,
    }

    def external_connection(self, cr, uid, id, debug=False, context=None):
        if isinstance(id, list):
            id=id[0]
        referential = self.browse(cr, uid, id)
        if 'wms_integration' in referential.type_id.name.lower():
            mo = re.search(r'ftp://(.*?):([0-9]+)', referential.location)
            if not mo:
                _logger.error('Referential location could not be parsed as an FTP URI: %s' % (referential.location,))
                return False
            (host, port) = mo.groups()
            conn = Connection(username=referential.apiusername, password=referential.apipass, host=host, port=port, debug=debug)
            return conn or False
        else:
            return super(external_referential, self).external_connection(cr, uid, id, DEBUG=DEBUG, context=context)

    def connect(self, cr, uid, id, context=None):
        if isinstance(id, (list, tuple)):
            if not len(id) == 1:
                raise osv.except_osv(_("Error"), _("Connect should be only call with one id"))
            else:
                id = id[0]
            core_imp_conn = self.external_connection(cr, uid, id, DEBUG, context=context)
            if core_imp_conn.connect():
                return core_imp_conn
            else:
                raise osv.except_osv(_("Connection Error"), _("Could not connect to server\nCheck location, username & password."))

        return False

    def core_sync(self, cr, uid, ids, context=None):
        filter = []
        for referential_id in ids:
            core_imp_conn = self.external_connection(cr, uid, referential_id, DEBUG, context=context)
            # TODO I don't think this will work. Each of these exports
            # needs a different path, but the external.referential has
            # only one location field. CUrrently, you're storing the
            # FTP path in location. The FTP paths will need to be
            # separated out, possibly into
            # external.mappings. (Alternatively, maybe we should
            # create one external referential for each export type?
            # This is not such a good idea as it's different to the
            # existing implementations of this.)
            self.pool.get('product.product').wms_import_base(cr, uid, core_imp_conn, referential_id, defaults={'referential_id': referential_id})
            self.pool.get('purchase.purchase.order').wms_import_base(cr, uid, core_imp_conn, referential_id, defaults={'referential_id': referential_id})
            self.pool.get('sale.sale.order').wms_import_base(cr, uid, core_imp_conn, referential_id, defaults={'referential_id': referential_id})
            self.pool.get('stock.dispatch').wms_import_base(cr, uid, core_imp_conn, referential_id, defaults={'referential_id': referential_id})

    def _get_path_from_referential(self, cr, uid, referential, context=None):
        mo = re.search(r'ftp://.*?:[0-9]+(.+)', referential.location)
        if not mo:
            _logger.error('Referential location could not be parsed as an FTP URI: %s' % (referential.location,))
            raise osv.except_osv(_("Connection Error"), _('Referential location could not be parsed as an FTP URI: %s' % (referential.location,)))
            # TODO Report error
        (path,) = mo.groups()
        return path
        
    def _export_all(self, cr, uid, model_name, context=None):
        # FIXME What's a better way to find the wms_integration
        # referentials?
        referential_ids = [r for r in self.search(cr, uid, []) if r.type_id.name.lower() == 'wms_integration']
        
        obj = self.pool.get(model_name)
        ids = obj.search(cr, uid, [])
        
        for referential in self.browse(cr, uid, referential_ids, context=context):
            conn = referential.external_connection(cr, uid, referential_ids, DEBUG, context)
            path = self._get_path_from_referential(cr, uid, referential, context)
            mapping_ids = self.pool.get('external.mapping').search(cr, uid, [('referential_id','=',referential.id),('model_id','=',model_name)])
            columns = self.pool.get('external.mapping').browse(cr, uid, mapping_ids[0]).get_column_headers()
            conn.init_export(remote_csv_fn=path, external_key_name=referential.external_key_name, column_headers=columns, required_fields=columns)
            conn.call(referential.create_method, [res for res in obj.read(cr, uid, ids, columns, context=context)])
            conn.finalize_export()
        return True
        
    def export_products(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        if self._export_all(cr, uid, 'product.product'):
            # import the confirmation CSV
            conn = referential.external_connection(cr, uid, ids, DEBUG, context)

            self.write(cr, uid, # last_products_export_time)

    def export_purchase_orders(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        return self._export_all(cr, uid, 'purchase.purchase.order')

    def export_sale_orders(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        return self._export_all(cr, uid, 'sale.sale.order')

    def export_dispatches(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        return self._export_all(cr, uid, 'stock.dispatch')

external_referential()
