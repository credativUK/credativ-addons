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
from external_referential_csvftp import Connection, ExternalReferentialError

import re
import logging
import datetime

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
                reporter.log_system_fail(cr, uid, 'external.referential', 'connect', id, exc=None, msg=msg, context=context)
            raise osv.except_osv(_('Configuration error'), _(msg))
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
        if not conn:
            raise osv.except_osv(_('Connection error'), _('Error establishing connection to external referential.'))

        mapping_ids = context.get('external_mapping_ids', False)
        if not mapping_ids:
            mapping_ids = self.pool.get('external.mapping').search(cr, uid, [('referential_id','=',referential_id),('model_id','=',model_name)])
        if not mapping_ids:
            raise osv.except_osv(_('Configuration error'), _('No mappings found for the referential "%s" of type "%s"' % (referential.name, referential.type_id.name)))

        res = {}
        self._exported = {}
        mapping_obj = self.pool.get('external.mapping')
        for mapping in mapping_obj.browse(cr, uid, mapping_ids):
            res[mapping.id] = False
            self._exported[mapping.id] = []

            # prepare the export file name
            now = datetime.datetime.now()
            export_uri_params = {'year': now.strftime('%Y'), 'month': now.strftime('%m'), 'day': now.strftime('%d'),
                                 'hour': now.strftime('%H'), 'minute': now.strftime('%M'), 'second': now.strftime('%S')}
            export_uri_params.update(context)
            remote_csv_fn = mapping.external_export_uri.format(**export_uri_params)

            # initialise the external referential export
            ext_columns = mapping_obj.get_ext_column_headers(cr, uid, mapping.id, context=context)
            conn.init_export(remote_csv_fn=remote_csv_fn, oe_model_name=mapping.model_id.name, external_key_name=mapping.external_key_name, column_headers=ext_columns, required_fields=[])

            # export the model data
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
                    export_data.append((obj_data['id'], data))

                    # create ir_model_data record if necessary
                    if obj_data['id'] not in update_res_ids:
                        ir_model_data_rec = {
                            'name': model_name.replace('.', '_') + '/' + data[mapping.external_key_name],
                            'model': model_name,
                            'res_id': obj_data['id'],
                            'external_referential_id': referential_id,
                            'module': 'extref/' + referential.name}
                        ir_model_data_rec_id = ir_model_data_obj.create(cr, uid, ir_model_data_rec)
                        self._exported[mapping.id].append(ir_model_data_rec_id)
                        if DEBUG:
                            _logger.debug('CSV export: %s #%s not previously exported; created new ir_model_data #%s' % (model_name, obj_data['id'], ir_model_data_rec_id))
                    else:
                        if DEBUG:
                            _logger.debug('CSV export: %s #%s previously exported' % (model_name, obj_data['id']))
                except Exception, X:
                    _logger.error(str(X))
                    report_line_obj.log_failed(cr, uid, model_name, 'export', referential_id, res_id=obj_data['id'], defaults={}, context=context)

            try:
                conn.call(mapping.external_create_method, records=export_data)
                conn.finalize_export()
            except ExternalReferentialError, X:
                for res_id in X.res_ids:
                    report_line_obj.log_failed(cr, uid, X.model_name, 'export', referential_id, res_id=res_id, defaults={}, context=context)
                self._undo_export(cr, uid, referential_id, model_name, res_ids, context=context)
            except Exception, X:
                self._undo_export(cr, uid, referential_id, model_name, context=context)
                raise osv.except_osv(_('Export error'), X.message)

            res[mapping.id] = True

        # Once the export has completed successfully, reset the list
        # of exported records
        self._exported = {}

        return all(res.values())

    def _undo_export(self, cr, uid, referential_id, model_name, res_ids=None, context=None):
        '''
        On a failure that prevents data from being transferred to the
        remote system, this method should be called to unmark any
        exported records.
        '''
        if context is None:
            context = {}

        if not hasattr(self, '_exported'):
            return

        res_ids = res_ids or None

        data_pool = self.pool.get('ir.model.data')
        for mapping_id, exported in self._exported.items():
            if res_ids:
                exported = list(set(exported) & set(res_ids))
            data_pool.unlink(cr, uid, exported, context=context)
            if DEBUG:
                _logger.debug('CSV export: Export failed, so removing ir_model_data records: %s' % (exported,))

        self._exported = {}

    def _get_exported_ids(self, cr, uid, referential_id, model_name, export_datetime, context=None):
        if context is None:
            context = {}

        referential_id = self._ensure_single_referential(cr, uid, referential_id, context=context)
        referential = self._ensure_wms_integration_referential(cr, uid, referential_id, context=context)

        table_name = model_name.replace('.', '_')
        cr.execute("""SELECT id FROM ir_model_data WHERE date_trunc('minute', %s) AND model=%s AND external_referential_id=%s""",
                   (export_datetime, table_name, referential_id))
        ir_model_data_ids = [r[0] for r in cr.fetchall()]
        ir_model_data_obj = self.pool.get('ir.model.data')
        return [d['res_id'] for d in ir_model_data_obj.read(cr, uid, ir_model_data_ids, fields=['res_id'])]
        
    def _get_last_exported_ids(self, cr, uid, referential_id, model_name, context=None):
        if context is None:
            context = {}

        referential_id = self._ensure_single_referential(cr, uid, referential_id, context=context)
        referential = self._ensure_wms_integration_referential(cr, uid, referential_id, context=context)

        table_name = model_name.replace('.', '_')
        cr.execute("""SELECT date_trunc('minute', max(create_date)) FROM ir_model_data WHERE model=%s AND external_referential_id=%s""",
                   (table_name, referential_id))
        res = cr.fetchone()
        if res and len(res) > 0:
            last_date = res[0]
            return self._get_exported_ids(cr, uid, referential_id, model_name, last_date, context=context)
        else:
            return []

    def _verify_export(self, cr, uid, export_mapping, exported_ids, success_fun, context=None):
        '''
        This method imports from the external WMS using the
        'verification'-type mapping associated with the supplied
        export_mapping. success_fun should be a Boolean function
        accepting two parameters. For each imported resource, this
        method applies success_fun to that resource and the
        corresponding exported resource. If success_fun returns False,
        the two resources are appended to a mistaches list. The method
        then returns a dictionary containing this list, a list of
        records which were exported but are missing from the imported
        confirmation resources, and a list of records which were
        confirmed but that were not exported. As well as returning
        this information, the method will also mark any successfully
        confirmed records as exported/confirmed in ir_model_data and
        generate external_report_lines for all the erroneous records.
        '''
        if context is None:
            context = {}

        # import the confirmation records
        conn = self.external_connection(cr, uid, export_mapping.referential_id, DEBUG, context=context)

        mapping_obj = self.pool.get('external.mapping')
        verification_mapping = mapping_obj.browse(cr, uid, export_mapping.external_verification_mapping.id, context=context)

        # prepare the import file name
        now = datetime.datetime.now()
        import_uri_params = {'year': now.strftime('%Y'), 'month': now.strftime('%m'), 'day': now.strftime('%d'),
                             'hour': now.strftime('%H'), 'minute': now.strftime('%M'), 'second': now.strftime('%S')}
        import_uri_params.update(context)
        remote_csv_fn = verification_mapping.external_import_uri.format(**import_uri_params)


        verification_columns = mapping_obj.get_ext_column_headers(cr, uid, verification_mapping.id)
        conn.init_import(remote_csv_fn=verification_mapping.external_import_uri,
                         oe_model_name=export_mapping.model_id.name,
                         external_key_name=verification_mapping.external_key_name,
                         column_headers=verification_columns)
        verification = conn.call(verification_mapping.external_list_method)
        conn.finalize_import()

        res = {'mismatch': [], 'missing': [], 'unexpected': []}

        # test the confirmation records against the exported records
        obj = self.pool.get(export_mapping.model_id.name)
        exported = dict([(r['id'], r) for r in obj.read(cr, uid, exported_ids)])
        ir_model_data_obj = self.pool.get(export_mapping.model_id.name)
        ir_model_data_exported_ids = ir_model_data_obj.search(cr, uid, [('external_referential_id','=',export_mapping.referential_id), ('model','=',export_mapping.model_id.name),('res_id','in',exported_ids)], context=context)
        res_ids = dict([(r['name'], r['res_id']) for r in ir_model_data_obj.read(cr, uid, ir_model_data_exported_ids, fields=['res_id','name'])])

        for conf_res in verification:
            res_id = res_ids.get(conf_res[export_mapping.external_key_name], None)
            exp_res = exported.get(res_id, None)
            if res_id and exp_res:
                if not success_fun(exp_res, conf_res):
                    res['mismatch'].append({'exported': exp_res, 'received': conf_res})
                else:
                    # TODO Mark the record as export confirmed
                    pass
            else:
                res['unexpected'].append({'exported': None, 'received': conf_res})

        # check for any missing records (i.e. exported but not
        # included in the confirmation receipt)
        received_ids = [r[verification_mapping.external_key_name] for r in verification]
        if set(exported_ids) > set(received_ids):
            missing = list(set(exported_ids) - set(received_ids))
            res['missing'] = [{'exported': {'res_id': exported[id]}, 'received': None} for id in missing]

        # Generate external_report_lines errors for all the erroneous
        # records
        report_line_obj = self.pool.get('external.report.line')
        error_types = {
            'mismatch':   ('exported', 'CSV export: Resource with ID "%s" failed the verification test.'),
            'missing':    ('exported', 'CSV export: Resource with ID "%s" was exported, but does not appear in confirmation receipt.'),
            'unexpected': ('received', 'CSV export: Resource with ID "%s" appears in confirmation receipt, but was not exported.')}
        for error, records in res:
            for r in records:
                (rec_type, msg) = error_types[error]
                msg = msg % r[rec_type]
                _logger.error(msg)
                report_line_obj.log_failed(cr, uid, export_mapping.model_id.name, 'verify', export_mapping.referential_id.id, res_id=r[rec_type]['res_id'], data_record=r[rec_type], context=context)

        return res

    def export_products(self, cr, uid, id, context=None):
        if context == None:
            context = {}
        if not 'search_params' in context:
            context['search_params'] = [('type', 'in', ('consu', 'product'))]
        return self._export(cr, uid, id, 'product.product', context=context)

external_referential()
