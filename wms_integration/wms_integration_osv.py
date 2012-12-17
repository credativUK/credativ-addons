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
from osv import osv,fields
from tools.translate import _
import netsvc
from base_external_referentials import external_osv

## TODO Decide whether ER_CSVFTP should be a separate addon or just a
## module in this addon
from external_referential_csvftp import Connection

import os
import re
import logging

_logger = logging.getLogger(__name__)

class wms_integration_osv(external_osv.external_osv):
    _name = "wms_integration_osv"

    def external_connection(self, cr, uid, referential):
        mo = re.search(r'ftp://(.*?):([0-9]+)', referential.location)
        if not mo:
            _logger.error('Referential location could not be parsed as an FTP URI: %s' % (referential.location,))
            return False
        (host, port) = mo.groups()
        conn = Connection(referential.apiusername, referential.apipass, host, port)
        return conn or False

    def sync_import(self, cr, uid, conn, external_referential_id, defaults={}, context={}):
        if not 'ids_or_filter' in context.keys():
            context['ids_or_filter'] = []
        result = {'create_ids': [], 'write_ids': []}
        mapping_id = self.pool.get('external.mapping').search(cr,uid,[('model','=',self._name),('referential_id','=',external_referential_id)])
        if mapping_id:
            ext_ref = self.pool.get('external.mapping').read(cr,uid,mapping_id[0],['import_src', 'export_src', 'external_key_name', 'external_list_method', 'column_headers', 'required_fields'])
            conn.init_sync(import_csv_fn=ext_ref['import_src'],
                           export_csv_fn=ext_ref['export_src'],
                           external_key_name=ext_ref['external_key_name'],
                           column_headers=ext_ref['column_headers'],
                           required_fields=ext_ref['required_fields'])
            data = []
            list_method = ext_ref.get('external_list_method',False)
            if list_method:
                data = conn.call(list_method, context['ids_or_filter'])


wms_integration_osv()
