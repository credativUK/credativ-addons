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
        'external_export_uri': fields.char('External export URI', size=200,
                                           help='For example, an FTP path pointing to a file name on the remote host.'),
        'external_import_uri': fields.char('External import URI', size=200,
                                           help='For example, an FTP path pointing to a file name on the remote host.'),
        # TODO The problem with using a mapping for the verification
        # CSV is that it doesn't actually map to any OpenERP model
        'external_verification_mapping': fields.many2one('external.mapping','External verification data format',
                                                         help='Mapping for export verification data to be imported from the remote host.'),
        'last_exported_time': fields.datetime('Last time exported')
        }

external_mapping()

class external_referential(wms_integration_osv.wms_integration_osv):
    _inherit = 'external.referential'

    _columns = {
        'active': fields.boolean('Active')
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

    def _export_all(self, cr, uid, model_name, context=None):
        if context is None:
            context = {}

        # FIXME What's a better way to find the wms_integration
        # referentials?
        referential_ids = [r for r in self.search(cr, uid, []) if r.type_id.name.lower() == 'wms_integration']
        
        obj = self.pool.get(model_name)
        ids = obj.search(cr, uid, [])
        
        # FIXME Why would there be more than one referential?
        for referential in self.browse(cr, uid, referential_ids, context=context):
            conn = referential.external_connection(cr, uid, referential_ids, DEBUG, context)
            mapping_ids = self.pool.get('external.mapping').search(cr, uid, [('referential_id','=',referential.id),('model_id','=',model_name)])
            for mapping in self.pool.get('external.mapping').browse(cr, uid, mapping_ids):
                # export the model data
                columns = mapping.get_column_headers()
                conn.init_export(remote_csv_fn=mapping.external_export_uri, external_key_name=mapping.external_key_name, column_headers=mapping.columns, required_fields=columns)
                export_data = [res for res in obj.read(cr, uid, ids, columns, context=context)]
                conn.call(mapping.external_create_method, export_data)
                conn.finalize_export()

                self._verify_export(cr, uid, mapping, [res.id for res in export_data], conn, context)

    def _verify_export(self, cr, uid, export_mapping, export_ids, conn, context=None):
        if context is None:
            context = {}

        verification_mapping = self.pool.get('external.mapping').browse(cr, uid, export_mapping.external_verification_mapping, context=context)
        verification_columns = verification_mapping.get_column_headers()
        conn.init_import(remote_csv_fn=verification_mapping.external_import_uri, external_key_name=verification_mapping.external_key_name, column_headers=verification_columns, required_fields=verification_columns)
        verification = conn.call(verification_mapping.external_list_method)

        return set(export_ids) == set([k for k in verification.keys()])

external_referential()
