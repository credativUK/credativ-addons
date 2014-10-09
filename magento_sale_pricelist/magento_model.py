# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright 2014 credativ Ltd
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

import logging
from openerp.osv import fields, orm
from datetime import datetime, timedelta
from openerp.addons.connector.session import ConnectorSession
from pricelist import pricelist_import_batch
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT

IMPORT_DELTA_BUFFER = 30  # seconds
_logger = logging.getLogger(__name__)


class magento_backend(orm.Model):
    ''' Inherit magento backend '''

    _inherit = 'magento.backend'

    _columns = {
        'import_pricelist_from_date': fields.datetime('Import Pricelists from date'),
    }

    def _scheduler_import_product_pricelist(self, cr, uid, domain=None, context=None):
        self._magento_backend(cr, uid, self.import_product_pricelist,
                              domain=domain, context=context)

    def import_product_pricelist(self, cr, uid, ids, context=None):
        """ Import Pricelist from all websites """
        if not hasattr(ids, '__iter__'):
            ids = [ids]
        self.check_magento_structure(cr, uid, ids, context=context)
        website_pool = self.pool.get('magento.website')
        for backend in self.browse(cr, uid, ids, context=context):
            import_start_time = datetime.now()
            for website in backend.website_ids:
                #Import pricelist for website
                website_pool.import_product_pricelist(cr, uid, website.id,
                                                      context=context)
            next_time = import_start_time - timedelta(seconds=IMPORT_DELTA_BUFFER)
            next_time = next_time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
            self.write(cr, uid, ids, {'import_pricelist_from_date': next_time},
                    context=context)
        return True

class magento_storeview(orm.Model):
    ''' Inherit magento store view '''

    _inherit = 'magento.storeview'

    _columns = {
        'pricelist_id': fields.many2one(
                'product.pricelist',
                string='Magento Pricelist',
                #readonly=True,
                help='Magento Pricelist asssociated with store view'),
        'import_pricelist_from_date': fields.datetime('Import Pricelists from date'),
        'sync_pricelist': fields.boolean('Sync Pricelist',
                help='If checked then it will synchronize pricelist for this store view. Note: Synchronization only happens one way Magento -> Openerp'),
    }

    def import_product_pricelist(self, cr, uid, ids, context=None):
        """ Import Pricelist from all websites """

        if not hasattr(ids, '__iter__'):
            ids = [ids]

        session = ConnectorSession(cr, uid, context=context)
        for storeview in self.browse(cr, uid, ids, context=context):
            import_start_time = datetime.now()
            if not storeview.sync_pricelist:
                continue
            if storeview.import_pricelist_from_date:
                from_date = datetime.strptime(
                    storeview.import_pricelist_from_date,
                    DEFAULT_SERVER_DATETIME_FORMAT)
            else:
                from_date = None
            pricelist_import_batch.delay(
                session, 'magento.product.pricelist', storeview.backend_id.id,
                {'magento_store_view_id': int(storeview.magento_id),
                    'from_date': from_date,
                    'store_view_id': int(storeview.id)})
            next_time = import_start_time - timedelta(seconds=IMPORT_DELTA_BUFFER)
            next_time = next_time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
            self.write(cr, uid, ids, {'import_pricelist_from_date': next_time},
                    context=context)
        return True

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
