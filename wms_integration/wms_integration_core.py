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

class external_referential(wms_integration_osv.wms_integration_osv):
    _inherit = 'external.referential'

    _columns = {
        'active': fields.boolean('Active'),
        'timestamp_last':fields.char('Last time stamp',size=100)
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
            self.pool.get('product.product').wms_import_base(cr, uid, core_imp_conn, referential_id, defaults={'referential_id': referential_id})
            self.pool.get('purchase.purchase.order').wms_import_base(cr, uid, core_imp_conn, referential_id, defaults={'referential_id': referential_id})
            self.pool.get('stock.dispatch').wms_import_base(cr, uid, core_imp_conn, referential_id, defaults={'referential_id': referential_id})

external_referential()

class external_product(wms_integration_osv.wms_integration_osv):
    _inherit = "product.product"

external_product()

class external_purchase_order(wms_integration_osv.wms_integration_osv):
    _inherit = "purchase.purchase_order"

external_purchase_order()

class external_dispatch(wms_integration_osv.wms_integration_osv):
    _inherit = "stock.dispatch"

external_dispatch()
