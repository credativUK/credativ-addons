# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution	
#    Copyright (C) 2013 credativ ltd (<http://www.credativ.co.uk>). All Rights Reserved
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
import pooler
from osv import osv, fields
from tools.translate import _

import datetime

import logging
_logger = logging.getLogger(__name__)

class external_log(osv.osv):
    _name = 'external.log'
    _description = 'External referential transfer log'
    _order = 'start_time desc'

    _columns = {
        'name': fields.char('Execution reference', type='char', size=15, required=True),
        'referential_id': fields.many2one('external.referential', 'External referential', required=True, readonly=True),
        'mapping_id': fields.many2one('external.mapping', 'External mapping', required=True, readonly=True),
        'retry_of': fields.many2one('external.log', 'Retry of', readonly=True),
        'start_time': fields.datetime('Start time', required=True, readonly=True),
        'end_time': fields.datetime('End time', readonly=True),
        'status': fields.selection([('in-progress', 'In progress'),
                                    ('transfer-failed', 'Transfer failed'),
                                    ('imported-fail', 'Imported - with errors'),
                                    ('imported-success', 'Imported - correct'),
                                    ('exported-fail', 'Exported - with errors'),
                                    ('exported-success', 'Exported - correct'),
                                    ('complete-rejections', 'Complete - rejections'),
                                    ('complete-complete', 'Complete')], string='Status', required=True, readonly=True),
        'model_id': fields.many2one('ir.model', 'Model', readonly=True),
        'create_uid': fields.many2one('res.users', 'User', readonly=True),
        'line_ids': fields.one2many('external.report.line', 'external_log_id', 'Report lines')
        }

    _defaults = {
        'name': lambda self, cr, uid, context: self.pool.get('ir.sequence').next_by_code(cr, uid, 'extref_exec_id', context=context)
        }

    _allowed_status_moves = [
        ('in-progress', 'transfer-failed'),
        ('in-progress', 'imported-failed'),
        ('in-progress', 'imported-success'),
        ('in-progress', 'exported-fail'),
        ('in-progress', 'exported-success'),
        ('imported-success', 'complete-rejections'),
        ('imported-success', 'complete-complete'),
        ('exported-success', 'complete-rejections'),
        ('exported-success', 'complete-complete')
        ]

    def start_transfer(self, cr, uid, ids, referential_id, model_name, context=None):
        if context is None:
            context = {}

        extref_pool = self.pool.get('external.referential')
        referential = extref_pool.browse(cr, uid, referential_id)

        # get the model from the given name
        try:
            model_id = self.pool.get('ir.model').search(cr, uid, [('model','=',model_name)], context=context)[0]
        except:
            raise osv.except_osv(_('Configuration error'), _('Could not find model: "%s"' % (model_name,)))

        # try and work out what mapping is going to be used

        # FIXME In principle, more than one mapping could be used; we
        # are currently assuming that just one will be used
        mapping_ids = context.get('external_mapping_ids', False)
        if not mapping_ids:
            mapping_ids = self.pool.get('external.mapping').search(cr, uid, [('referential_id','=',referential_id),
                                                                             ('model_id','=',model_name)], context=context)
        if not mapping_ids:
            raise osv.except_osv(_('Configuration error'),
                                 _('No mappings found for the referential "%s" of type "%s"' %\
                                       (referential.name, referential.type_id.name)))
        if len(mapping_ids) > 1:
            _logger.warn('Found multiple candidate mappings for referential "%s", model "%s"' %\
                             (referential.name, model_name))

        try:
            log_cr = pooler.get_db(cr.dbname).cursor()
            log_id = self.create(log_cr, uid, {'referential_id': referential_id,
                                               'mapping_id': mapping_ids[0],
                                               'retry_of': context.get('retry_of_execution', None),
                                               'start_time': datetime.datetime.now(),
                                               'status': 'in-progress',
                                               'model_id': model_id}, context=context)
        except:
            log_cr.rollback()
            raise
        else:
            log_cr.commit()
        finally:
            log_cr.close()
        return log_id

    def end_transfer(self, cr, uid, ids, force_status=None, context=None):
        if context is None:
            context = {}

        if isinstance(ids, (list, tuple)):
            ids = ids[0]

        try:
            log_cr = pooler.get_db(cr.dbname).cursor()
            log = self.browse(log_cr, uid, ids)

            if not log:
                raise ValueError('Cannot call end_transfer on non-existant log: %d' % (ids,))

            # FIXME Needs to account for import and confirmation
            # operations
            new_status = force_status or all([line.state in ['exported', 'updated'] for line in log.line_ids]) and 'exported-success' or 'exported-fail'
            if (log.status, new_status) in self._allowed_status_moves:
                self.write(log_cr, uid, ids, {'end_time': datetime.datetime.now(), 'status': new_status})
            else:
                _logger.warn('Cannot update transfer log status from "%s" to "%s"; status change ignored.' % (log.status, new_status))
        except:
            log_cr.rollback()
            raise
        else:
            log_cr.commit()
        finally:
            log_cr.close()

    def import_confirmation(self, cr, uid, ids, context=None):
        if context is None:
            context = {}

        if isinstance(ids, (list, tuple)):
            ids = ids[0]

        extref_pool = self.pool.get('external.referential')

        log = self.browse(cr, uid, ids, context=context)
        if not log:
            # FIXME
            return

        referential = extref_pool.browse(cr, uid, log.referential_id.id, context=context)
        exported_ids = extref_pool._get_exported_ids_by_log(cr, uid, log.referential_id.id, log.model_id.model, ids, context=context)
        if exported_ids:
            return extref_pool._verify_export(cr, uid, log.mapping_id, exported_ids, success_fun=lambda *a: True, context=context)
        else:
            _logger.warn('Found no exported records for log %s to confirm' % (log.name,))

external_log()


class external_referential(osv.osv):
    _inherit = 'external.referential'

    _columns = {
        'external_log_ids': fields.one2many('external.log', 'referential_id', 'External log entries')
        }

external_referential()


class external_report_lines(osv.osv):
    _inherit = 'external.report.line'

    def _get_resource_name(self, cr, uid, ids, field_names, args, context=None):
        if not ids: return {}
        res = {}
        if context is None:
            context = {}
        for line in self.browse(cr, uid, ids, context=context):
            if line.res_id != 0:
                record = False
                model_pool = False
                if line.res_model:
                    model_pool = self.pool.get(line.res_model)
                if model_pool:
                    record = model_pool.read(cr, uid, line.res_id, ['name'], context=context)
                if record:
                    res[line.id] = record['name']
                else:
                    res[line.id] = '<NOT FOUND>'
            else:
                res[line.id] = '<DEFAULT>'
        return res

    _columns = {
        'state': fields.selection([('exported','Exported'),
                                   ('updated', 'Updated'),
                                   ('failed','Failed'),
                                   ('confirmed','Confirmed'),
                                   ('rejected','Rejected')], readonly=True, string='State'),
        'res_name': fields.function(_get_resource_name, type='char', size=128, string='Resource Name'),
        'external_log_id': fields.many2one('external.log', 'External log', readonly=True),
        'message': fields.text('Error message', readonly=True)
        }

    def log_system_fail(self, cr, uid, model, action, referential_id, exc, msg=None, defaults=None, context=None):
        defaults = defaults or {}
        context = context or {}
        exc = exc or Exception(msg)

        log_cr = pooler.get_db(cr.dbname).cursor()

        try:
            origin_defaults = defaults.copy()
            origin_context = context.copy()
            # connection object cannot be kept in text
            if origin_context.get('conn_obj', False):
                del origin_context['conn_obj']
            info = self._prepare_log_info(
                log_cr, uid, origin_defaults, origin_context, context=context)
            vals = self._prepare_log_vals(
                log_cr, uid, model, action, res_id=None, external_id=None,
                referential_id=referential_id, data_record=None, context=context)
            vals.update(info)
            vals['message'] = msg
            vals['external_log_id'] = context.get('external_log_id')
            _logger.debug('Create system fail with vals: %s' % (vals,))
            report = self.create(log_cr, uid, vals, context=context)
        except:
            log_cr.rollback()
            raise
        else:
            log_cr.commit()
        finally:
            log_cr.close()
        return report

    def log_system_success(self, cr, uid, model, action, referential_id, context=None):
        raise NotImplementedError()

    def retry_system(self, cr, uid):
        raise NotImplementedError()

    def _log(self, cr, uid, model, action, referential_id, state, res_id=None, external_id=None, data_record=None, defaults=None, context=None):
        defaults = defaults or {}
        context = context or {}

        log_cr = pooler.get_db(cr.dbname).cursor()

        try:
            origin_defaults = defaults.copy()
            origin_context = context.copy()
            # connection object cannot be serialised
            if origin_context.get('conn_obj', False):
                del origin_context['conn_obj']
            info = self._prepare_log_info(log_cr, uid, origin_defaults, origin_context, context=context)
            vals = self._prepare_log_vals(log_cr, uid, model, action, res_id=res_id, external_id=external_id,
                                          referential_id=referential_id, data_record=data_record, context=context)
            vals.update(info)
            vals['state'] = state
            vals['external_log_id'] = context.get('external_log_id')
            report = self.create(log_cr, uid, vals, context=context)
        except:
            log_cr.rollback()
            raise
        else:
            log_cr.commit()
        finally:
            log_cr.close()
        return report
        
    def log_exported(self, cr, uid, model, action, referential_id, res_id=None, external_id=None, data_record=None, defaults=None, context=None):
        return self._log(cr, uid, model, action, referential_id, 'exported', res_id=res_id, external_id=external_id, data_record=data_record, defaults=defaults, context=context)

    def log_updated(self, cr, uid, model, action, referential_id, res_id=None, external_id=None, data_record=None, defaults=None, context=None):
        return self._log(cr, uid, model, action, referential_id, 'updated', res_id=res_id, external_id=external_id, data_record=data_record, defaults=defaults, context=context)

    def log_failed(self, cr, uid, model, action, referential_id, res_id=None, external_id=None, data_record=None, defaults=None, context=None):
        res = super(external_report_lines, self).log_failed(cr, uid, model, action, referential_id, res_id=res_id, external_id=external_id, data_record=data_record, defaults=defaults, context=context)
        # update the fail log with additional fields
        vals = {'state': 'failed'}
        if context.get('external_log_id'):
            vals['external_log_id'] = context.get('external_log_id')
        if res:
            self.write(cr, uid, res, vals)
        return res

    def log_success(self, cr, uid, model, action, referential_id, res_id=None, external_id=None,  data_record=None, defaults=None, context=None):
        # FIXME The super method actually removes the fail log, so we
        # probably don't actually want to do this
        #res = super(external_report_lines, self).log_success(cr, uid, model, action, referential_id, res_id, external_id, context)
        #return res

        return self._log(cr, uid, model, action, referential_id, 'confirmed', res_id=res_id, external_id=external_id, data_record=data_record, defaults=defaults, context=context)

    def log_rejected(self, cr, uid, model, action, referential_id, res_id=None, external_id=None, context=None):
        return self._log(cr, uid, model, action, referential_id, 'rejected', res_id=res_id, external_id=external_id, context=context)

    def retry(self, cr, uid, ids, context=None):

        res = super(external_report_lines, self).retry(cr, uid, ids, context)
        return res

external_report_lines()


class ir_model_data(osv.osv):
    _inherit = 'ir.model.data'
    
    _columns = {
        'external_log_id': fields.integer('Execution ID', help='Unique ID of the execution of the extref under which this record was imported/exported')
        }
    
ir_model_data()
