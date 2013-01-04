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

    def get_ext_column_headers(self, cr, uid, ids, context=None):
        if not isinstance(ids, list):
            ids = [ids]

        res = []
        line_ids = self.pool.get('external.mapping.line').search(cr, uid, [('mapping_id','=',ids[0])])
        for line in self.pool.get('external.mapping.line').browse(cr, uid, line_ids):
            res.append((line.sequence, line.external_field))

        return [f for s, f in sorted(res, lambda a, b: cmp(a[0], b[0]))]

    def get_oe_column_headers(self, cr, uid, ids, context=None):
        if not isinstance(ids, list):
            ids = [ids]

        res = []
        line_ids = self.pool.get('external.mapping.line').search(cr, uid, [('mapping_id','=',ids[0])])
        for line in self.pool.get('external.mapping.line').browse(cr, uid, line_ids):
            res.append(line.field_id.name)

        return res

    def oe_keys_to_ext_keys(self, cr, uid, ids, oe_rec, context=None):
        if not isinstance(ids, list):
            ids = [ids]

        line_ids = self.pool.get('external.mapping.line').search(cr, uid, [('mapping_id','=',ids[0])])
        defaults = {}
        referential_id = self.read(cr, uid, ids[0], ['referential_id'], context)['referential_id'][0]
        mapping_lines = self.pool.get('external.mapping.line').read(cr, uid, line_ids, ['external_field', 'out_function'])
        rec = self.extdata_from_oevals(cr, uid, referential_id, oe_rec, mapping_lines, defaults, context)
        
        return rec

    def ext_keys_to_oe_keys(self, cr, uid, ids, ext_rec, context=None):
        if not isinstance(ids, list):
            ids = [ids]

        rec = {}
        line_ids = self.pool.get('external.mapping.line').search(cr, uid, [('mapping_id','=',ids[0])])
        for line in self.pool.get('external.mapping.line').browse(cr, uid, line_ids):
            rec[line.field_id.name] = ext_rec[line.external_field]

        return rec

    _columns = {
        'purpose': fields.selection([('data', 'Data'), ('verification', 'Verification')], 'Mapping usage', required=True),
        'external_export_uri': fields.char('External export URI', size=200,
                                           help='For example, an FTP path pointing to a file name on the remote host.'),
        'external_import_uri': fields.char('External import URI', size=200,
                                           help='For example, an FTP path pointing to a file name on the remote host.'),
        'external_verification_mapping': fields.many2one('external.mapping','External verification data format', domain=[('purpose','=','verification')],
                                                         help='Mapping for export verification data to be imported from the remote host.'),
        'last_exported_time': fields.datetime('Last time exported')
        }

    _defaults = {
        'purpose': lambda *a: 'data'
    }

external_mapping()

class external_mapping_line(osv.osv):
    _inherit = 'external.mapping.line'

    _columns = {
        'sequence': fields.integer('Position in field order', required=True,
                                   help='Assign sequential numbers to each line to indicate their required order in the output data.')
        }

    _sql_constraints = [
        ('sequence', 'unique(mapping_id, sequence)', 'Sequence number must be unique.')
        ]
    
    _order = 'sequence'

external_mapping_line()

class external_referential(wms_integration_osv.wms_integration_osv):
    _inherit = 'external.referential'

    def _ensure_single_referential(self, cr, uid, id, context=None):
        if context is None:
            context = {}
        if isinstance(id, (list, tuple)):
            if not len(id) == 1:
                raise osv.except_osv(_("Error"), _("External referential connection methods should only called with only one id"))
            else:
                return id[0]
        else:
            return id
    
    def _ensure_wms_integration_referential(self, cr, uid, id, context=None):
        if context is None:
            context = {}
        # FIXME What's a better way of selecting the right external referential?
        if isinstance(id, int):
            referential = self.browse(cr, uid, id, context=context)
            if 'external wms' in referential.type_id.name.lower():
                return referential
            else:
                return False

    _columns = {
        'active': fields.boolean('Active'),
        }

    _defaults = {
        'active': lambda *a: 1,
    }

    def external_connection(self, cr, uid, id, DEBUG=False, context=None):
        if context is None:
            context = {}

        reporter = context.pop('reporter', None)

        id = self._ensure_single_referential(cr, uid, id, context=context)
        referential = self._ensure_wms_integration_referential(cr, uid, id, context=context)
        if not referential:
            return super(external_referential, self).external_connection(cr, uid, id, DEBUG=DEBUG, context=context)

        mo = re.search(r'ftp://(.*?):([0-9]+)', referential.location)
        if not mo:
            msg = 'Referential location could not be parsed as an FTP URI: %s' % (referential.location,)
            _logger.error(msg)
            if reporter:
                reporter.log_system_fail(cr, uid, None, 'connect', id, exc=None, msg=msg, context=context)
            return False
        (host, port) = mo.groups()

        csv_opts = getattr(referential, 'output_options', {})
        csv_opts['fieldproc'] = self.make_fieldproc(csv_opts)

        conn = Connection(username=referential.apiusername,
                          password=referential.apipass,
                          referential_id=id,
                          cr=cr,
                          uid=uid,
                          host=host,
                          port=int(port),
                          csv_writer_opts=csv_opts,
                          reporter=reporter,
                          debug=DEBUG)
        return conn or False

    def connect(self, cr, uid, id, context=None):
        if context is None:
            context = {}

        id = self._ensure_single_referential(cr, uid, id, context=context)
        referential = self._ensure_wms_integration_referential(cr, uid, id, context=context)
        if not referential:
            return super(external_referential, self).external_connection(cr, uid, id, DEBUG=DEBUG, context=context)

        core_imp_conn = self.external_connection(cr, uid, id, DEBUG, context=context)
        if core_imp_conn.connect():
            return core_imp_conn
        else:
            raise osv.except_osv(_("Connection Error"), _("Could not connect to server\nCheck location, username & password."))

    def make_fieldproc(self, output_opts):
        def strip_delimiter(field):
            if isinstance(field, (str, unicode)):
                return field.replace(output_opts.get('delimier',','),'')
            else:
                return field
        return strip_delimiter

    def _export(self, cr, uid, referential_id, model_name, res_ids=None, context=None):
        if context is None:
            context = {}

        referential_id = self._ensure_single_referential(cr, uid, referential_id, context=context)
        referential = self._ensure_wms_integration_referential(cr, uid, referential_id, context=context)
        report_line_obj = self.pool.get('external.report.line')
        context['use_external_log'] = True
        context['reporter'] = report_line_obj

        obj = self.pool.get(model_name)
        res_ids = res_ids or obj.search(cr, uid, context.get('search_params',[]), context=context)

        # find which of the supplied res_ids are updates
        ir_model_data_obj = self.pool.get('ir.model.data')
        ir_model_data_ids = ir_model_data_obj.search(cr, uid, [('external_referential_id','=',referential_id),('model','=',model_name),('res_id','in',res_ids)], context=context)
        update_res_ids = [d['res_id'] for d in ir_model_data_obj.read(cr, uid, ir_model_data_ids, fields=['res_id'])]
        
        conn = self.external_connection(cr, uid, referential_id, DEBUG, context=context)
        mapping_ids = self.pool.get('external.mapping').search(cr, uid, [('referential_id','=',referential_id),('model_id','=',model_name)])
        if not mapping_ids:
            raise osv.except_osv(_('Configuration error'), _('No mappings found for the referential "%s" of type "%s"' % (referential.name, referential.type_id.name)))

        res = {}
        mapping_obj = self.pool.get('external.mapping')
        for mapping in mapping_obj.browse(cr, uid, mapping_ids):
            # export the model data
            ext_columns = mapping_obj.get_ext_column_headers(cr, uid, mapping.id, context=context)
            conn.init_export(remote_csv_fn=mapping.external_export_uri, oe_model_name=mapping.model_id.name, external_key_name=mapping.external_key_name, column_headers=ext_columns, required_fields=ext_columns)
            export_data = []
            for obj_data in obj.read(cr, uid, res_ids, [], context=context):
                try:
                    if obj_data['id'] in update_res_ids:
                        obj_data['ext_id'] = True
                    # convert record key names from oe model to external model
                    data = mapping_obj.oe_keys_to_ext_keys(cr, uid, mapping.id, obj_data, context=context)

                    # don't export records that don't have a key name field value
                    if data[mapping.external_key_name].strip() == '':
                        msg = 'CSV export: %s #%s has no %s value; will not export' % (model_name, obj_data['id'], mapping.external_key_name)
                        _logger.error(msg)
                        report_line_obj.log_failed(cr, uid, model_name, 'export', referential_id, res_id=obj_data['id'], defaults={}, context=context)
                        continue

                    # add record to export list
                    export_data.append(data)

                    # create ir_model_data record if necessary
                    if obj_data['id'] not in update_res_ids:
                        ir_model_data_rec = {
                            'name': model_name.replace('.', '_') + '/' + data[mapping.external_key_name],
                            'model': model_name,
                            'res_id': obj_data['id'],
                            'external_referential_id': referential_id,
                            'module': 'extref/' + referential.name}
                        ir_model_data_rec_id = ir_model_data_obj.create(cr, uid, ir_model_data_rec)
                        if DEBUG:
                            _logger.debug('CSV export: %s #%s not previously exported; created new ir_model_data #%s' % (model_name, obj_data['id'], ir_model_data_rec_id))
                    else:
                        if DEBUG:
                            _logger.debug('CSV export: %s #%s previously exported' % (model_name, obj_data['id']))
                except Exception, X:
                    _logger.error(str(X))
                    report_line_obj.log_failed(cr, uid, model_name, 'export', referential_id, res_id=obj_data['id'], defaults={}, context=context)
                
            conn.call(mapping.external_create_method, records=export_data)
            conn.finalize_export()

            if mapping.external_verification_mapping:
                # TODO Defer the verification by some delay
                res[mapping.id] = self._verify_export(cr, uid, mapping, [res[mapping.external_key_name] for res in export_data], conn, context)
            else:
                _logger.info('CSV export: Mapping has no verification mapping defined.')

        return all(res.values())

    def _export_many(self, cr, uid, referential_id, model_name, export_ref_func, res_ids=None, context=None):
        '''
        This method exports each resource individually (e.g. a single file).
        '''

    def _verify_export(self, cr, uid, export_mapping, export_ids, conn, context=None):
        if context is None:
            context = {}

        mapping_obj = self.pool.get('external.mapping')
        verification_mapping = mapping_obj.browse(cr, uid, export_mapping.external_verification_mapping.id, context=context)
        verification_columns = mapping_obj.get_ext_column_headers(cr, uid, verification_mapping.id)
        conn.init_import(remote_csv_fn=verification_mapping.external_import_uri, oe_model_name=export_mapping.model_id.name, external_key_name=verification_mapping.external_key_name, column_headers=verification_columns)
        verification = conn.call(verification_mapping.external_list_method)
        conn.finalize_import()

        received_ids = [r[verification_mapping.external_key_name] for r in verification]
        if set(export_ids) == set(received_ids):
            return True
        else:
            missing = list(set(export_ids) - set(received_ids))
            msg = 'CSV export: Verification IDs returned by server did not match sent IDs. Missing: %d.' % (len(missing),)
            _logger.error(msg)
            report_line_obj = self.pool.get('external.report.line')
            report_line_obj.log_system_fail(cr, uid, export_mapping.model_id.name, 'verify', export_mapping.referential_id.id, exc=None, msg=msg, context=context)
            return False

    def export_products(self, cr, uid, id, context=None):
        if context == None:
            context = {}
        if not 'search_params' in context:
            context['search_params'] = [('type', 'in', ('consu', 'product'))]
        return self._export(cr, uid, id, 'product.product', context=context)

external_referential()
