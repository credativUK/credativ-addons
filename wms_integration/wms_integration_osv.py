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

import re
import logging

_logger = logging.getLogger(__name__)
DEBUG = True

class wms_integration_osv(osv.osv):
    _register = False

    def wms_import_base(self, cr, uid, conn, external_referential_id, defaults=None, context=None):
        if context is None:
            context = {}
        if defaults is None:
            defaults = {}
        if not 'ids_or_filter' in context.keys():
            context['ids_or_filter'] = []
        result = {'create_ids': [], 'write_ids': []}
        mapping_id = self.pool.get('external.mapping').search(cr, uid, [('model','=',self._name), ('referential_id','=',external_referential_id)])
        if mapping_id:
            #mapping = self.pool.get('external.mapping').read(cr, uid, mapping_id[0], ['location', 'external_key_name', 'external_list_method', 'column_headers', 'required_fields'])
            mapping = self.pool.get('external.mapping').browse(cr, uid, mapping_id[0])
            mo = re.search(r'ftp://.*?:[0-9]+(.+)', mapping.location)
            if not mo:
                _logger.error('Referential location could not be parsed as an FTP URI: %s' % (mapping.location,))
                raise osv.except_osv(_("Connection Error"), _('Referential location could not be parsed as an FTP URI: %s' % (mapping.location,)))
                # TODO Report error
            (path,) = mo.groups()
            
            conn.init_import(import_csv_fn=path,
                             external_key_name=mapping.external_key_name,
                             column_headers=mapping.get_column_headers(cr, uid, context=context),
                             required_fields=mapping.get_column_headers(cr, uid, context=context))
            data = []
            if context.get('id', False):
                get_method = mapping.get('external_get_method',False)
                if get_method:
                    data = [conn.call(get_method, [context.get('id', False)])]
                    data[0]['external_id'] = context.get('id', False)
                    result = self.ext_import(cr, uid, data, external_referential_id, defaults, context)
            else:
                list_method = mapping.get('external_list_method',False)
                if list_method:
                    data = conn.call(list_method, context['ids_or_filter'])
                    result = self.ext_import(cr, uid, data, external_referential_id, defaults, context)

        return result
        
    def get_external_data(self, cr, uid, conn, external_referential_id, defaults=None, context=None):
        if context is None:
            context = {}
        return self.wms_import_base(cr, uid, conn, external_referential_id, defaults, context)

def ext_create(self, cr, uid, data, conn, method, oe_id, context):
    if context is None: context = {}
    if context.get('ext_create_unpack_data', False):
        return conn.call(method, data)
    else:
        return conn.call(method, [data])

osv.osv.ext_create = ext_create

