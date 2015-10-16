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
from datetime import datetime, timedelta
from openerp.osv import fields, orm
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
from openerp.addons.connector.session import ConnectorSession
from pricelist import pricelist_import_batch

IMPORT_DELTA_BUFFER = 30  # seconds

_logger = logging.getLogger(__name__)


class magento_website(orm.Model):
    ''' Inherit magento website '''

    _inherit = 'magento.website'

    _columns = {
        'import_pricelist_from_date':fields.datetime(
            'Import Pricelist from date'
            ),
    }

    def _get_store_view_ids(self, cr, uid, website, context=None):
        ''' Get Magento store view ids from website object instance '''

        stores = website.store_ids or []
        storeviews = []
        [storeviews.extend(x.storeview_ids) for x in stores]
        magento_storeview_ids = [(i.id, i.magento_id) for i in storeviews if i.sync_pricelist]
        return magento_storeview_ids

    def import_product_pricelist(self, cr, uid, ids, context=None):
        if not hasattr(ids, '__iter__'):
            ids = [ids]
        import_start_time = datetime.now()
        storeview_obj = self.pool.get('magento.storeview')
        for website in self.browse(cr, uid, ids, context=context):
            backend_id = website.backend_id.id
            if website.import_pricelist_from_date:
                from_date = datetime.strptime(
                    website.import_pricelist_from_date,
                    DEFAULT_SERVER_DATETIME_FORMAT)
            else:
                from_date = None
            magento_storeview_ids = self._get_store_view_ids(cr,uid,website,context=context)
            #assert magento_storeview_ids, (
                #'No store view not found for website %s' %(website.name))
            # Product price in magento is defined on website level.
            # Price in magento can be defined on storeview level.
            for storeview_id, magento_store_view_id in magento_storeview_ids:
                storeview_obj.import_product_pricelist(cr, uid, storeview_id, context=context)

        # Records from Magento are imported based on their `created_at`
        # date.  This date is set on Magento at the beginning of a
        # transaction, so if the import is run between the beginning and
        # the end of a transaction, the import of a record may be
        # missed.  That's why we add a small buffer back in time where
        # the eventually missed records will be retrieved.  This also
        # means that we'll have jobs that import twice the same records,
        # but this is not a big deal because they will be skipped when
        # the last `sync_date` is the same.
        next_time = import_start_time - timedelta(seconds=IMPORT_DELTA_BUFFER)
        next_time = next_time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        self.write(cr, uid, ids, {'import_pricelist_from_date': next_time},
                   context=context)
        return True

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: