# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2013 credativ Ltd (<http://credativ.co.uk>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import base64
import simplejson
import logging
import time
import zlib
import thread
import threading
import sys

import openerp.pooler as pooler
import openerp.netsvc as netsvc
from openerp.service.web_services import report_spool
import openerp.exceptions
import openerp.tools as tools

from openerp.addons.web.controllers.main import Reports as ReportsBase
import openerp.addons.web.common as common
from openerp.addons.web.common.http import controllers_class, ControllerType
openerpweb = common.http

_logger = logging.getLogger(__name__)

class report_spool_named(report_spool):
    _filename_support = True

    def exp_report(self, db, uid, object, ids, datas=None, context=None):
        if not datas:
            datas={}
        if not context:
            context={}

        self.id_protect.acquire()
        self.id += 1
        id = self.id
        self.id_protect.release()

        self._reports[id] = {'uid': uid, 'result': False, 'state': False, 'exception': None}

        def go(id, uid, ids, datas, context):
            cr = pooler.get_db(db).cursor()
            try:
                obj = netsvc.LocalService('report.'+object)
                report_res = obj.create(cr, uid, ids, datas, context)
                if len(report_res) == 2:
                    (result, format) = report_res
                elif len(report_res) == 3:
                    (result, format, filename) = report_res
                    self._reports[id]['filename'] = filename
                if not result:
                    tb = sys.exc_info()
                    self._reports[id]['exception'] = openerp.exceptions.DeferredException('RML is not available at specified location or not enough data to print!', tb)
                self._reports[id]['result'] = result
                self._reports[id]['format'] = format
                self._reports[id]['state'] = True
            except Exception, exception:
                _logger.exception('Exception: %s\n', str(exception))
                if hasattr(exception, 'name') and hasattr(exception, 'value'):
                    self._reports[id]['exception'] = openerp.exceptions.DeferredException(tools.ustr(exception.name), tools.ustr(exception.value))
                else:
                    tb = sys.exc_info()
                    self._reports[id]['exception'] = openerp.exceptions.DeferredException(tools.exception_to_unicode(exception), tb)
                self._reports[id]['state'] = True
            cr.commit()
            cr.close()
            return True

        thread.start_new_thread(go, (id, uid, ids, datas, context))
        return id

    def _check_report(self, report_id):
        filename = self._reports[report_id].get('filename', None)
        res = super(report_spool_named, self)._check_report(report_id)
        if filename:
            res['filename'] = filename
        return res

class ControllerTypeOverride(ControllerType):
    def __init__(cls, name, bases, attrs):
        super(ControllerTypeOverride, cls).__init__(name, bases, attrs)
        controllers_class["%s.%s" % (cls._override, cls.__name__)] = cls
        report_spool_named()

class Reports(ReportsBase):
    __metaclass__ = ControllerTypeOverride
    _override = 'openerp.addons.web.controllers.main.Reports'

    @openerpweb.httprequest
    def index(self, req, action, token):
        action = simplejson.loads(action)

        report_srv = req.session.proxy("report")
        context = req.session.eval_context(
            common.nonliterals.CompoundContext(
                req.context or {}, action[ "context"]))

        report_data = {}
        report_ids = context["active_ids"]
        if 'report_type' in action:
            report_data['report_type'] = action['report_type']
        if 'datas' in action:
            if 'ids' in action['datas']:
                report_ids = action['datas'].pop('ids')
            report_data.update(action['datas'])

        report_id = report_srv.report(
            req.session._db, req.session._uid, req.session._password,
            action["report_name"], report_ids,
            report_data, context)

        report_struct = None
        while True:
            report_struct = report_srv.report_get(
                req.session._db, req.session._uid, req.session._password, report_id)
            if report_struct["state"]:
                break

            time.sleep(self.POLLING_DELAY)

        report = base64.b64decode(report_struct['result'])
        if report_struct.get('code') == 'zlib':
            report = zlib.decompress(report)
        report_mimetype = self.TYPES_MAPPING.get(
            report_struct['format'], 'octet-stream')

        filename = report_struct.get('filename', '%s.%s' % (action['report_name'], report_struct['format']))

        return req.make_response(report,
             headers=[
                 ('Content-Disposition', 'attachment; filename="%s"' % (filename,)),
                 ('Content-Type', report_mimetype),
                 ('Content-Length', len(report))],
             cookies={'fileToken': token})
