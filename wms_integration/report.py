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

class external_report_lines(osv.osv):
    _inherit = 'external.report.line'

    _columns = {
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

external_report_lines()
