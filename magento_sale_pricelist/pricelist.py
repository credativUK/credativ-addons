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
import magento as magentolib
from openerp.osv import orm, fields
from openerp.tools.translate import _
from openerp.addons.connector.queue.job import job, related_action
from openerp.addons.connector.unit.mapper import (mapping,
                                                  ImportMapper
                                                  )
from openerp.addons.magentoerpconnect.unit.backend_adapter import GenericAdapter
from openerp.addons.magentoerpconnect.connector import get_environment
from openerp.addons.magentoerpconnect.backend import magento
from openerp.addons.magentoerpconnect.unit.import_synchronizer import (
                                       DirectBatchImport,
                                       MagentoImportSynchronizer,
                                       )
from openerp.addons.magentoerpconnect.related_action import link
from openerp.addons.connector.connector import Binder
_logger = logging.getLogger(__name__)


class magento_product_pricelist(orm.Model):
    _name = 'magento.product.pricelist'
    _inherit = 'magento.binding'
    _inherits = {'product.pricelist': 'openerp_id'}
    _description = 'Magento Product Pricelist'

    _columns = {
        'openerp_id': fields.many2one('product.pricelist',
                                      string='pricelist',
                                      required=True,
                                      ondelete='restrict'),
        'created_at': fields.date('Created At (on Magento)'),
        'updated_at': fields.date('Updated At (on Magento)'),
        #TODO
        'magento_store_id': fields.char('Magento store ID', size=128),
        'magento_storeview_id': fields.char('Magento store view ID', size=128),
        }

    _sql_constraints = [
        ('magento_uniq', 'unique(backend_id, magento_id)',
         'A Pricelist with same ID already exists.'),
            ]

@magento
class ProductPricelistAdapter(GenericAdapter):
    _model_name = 'magento.product.pricelist'
    _magento_model = 'catalog_product'
    _admin_path = '/{model}/edit/id/{id}'

    def read(self, id, attributes=None):
        """ Returns the information of a record

        :rtype: dict
        """
        if not attributes:
            attributes = []
        attributes.append('price')
        storeview_id = self.session.context.get('magento_store_view_id')
        with magentolib.API(self.magento.location,
                            self.magento.username,
                            self.magento.password) as api:
            return api.call('%s.info' % self._magento_model,
                          [int(id), storeview_id, attributes, 'id'])

    def search(self, filters=None, from_date=None, magento_storeview_ids=None):
        """ Search records according to some criterias
        and returns a list of ids

        :rtype: list
        """
        if filters is None:
            filters = {}
        if from_date:
            filters['updated_at'] = {'from_date': from_date}
        #TODO Check if this can be used as checkpoint
        with magentolib.API(self.magento.location,
                            self.magento.username,
                            self.magento.password) as api:
            #Get list of magento product id
            params = filters and [filters] or [[]]
            params.extend(magento_storeview_ids)
            return [int(row['product_id']) for row
                       in api.call('%s.list' % 'catalog_product',
                            params)]
        return []

@job
def pricelist_import_batch(session, model_name, backend_id, filters=None):
    """ Prepare the import of Pricelist modified on Magento """
    if filters is None:
        filters = {}
    assert 'magento_store_view_id' in filters, (
            'Missing information about Magento store view ID')
    env = get_environment(session, model_name, backend_id)
    importer = env.get_connector_unit(PricelistBatchImport)
    importer.run(filters=filters)

@magento
class PricelistBatchImport(DirectBatchImport):
    """ Import the Magento Pricelist.

    For every pricelist in the list, a delayed job is created.
    """
    _model_name = ['magento.product.pricelist']

    def run(self, filters=None):
        """ Run the synchronization """

        from_date = filters.pop('from_date', None)
        magento_storeview_id = [filters.pop('magento_store_view_id')]
        record_ids = self.backend_adapter.search(filters,
                                                 from_date,
                                                 magento_storeview_id)
        _logger.info('search for magento Pricelist  %s returned %s',
                     filters, record_ids)

        for record_id in record_ids:
            self._import_record(record_id)

@magento
class PricelistImport(MagentoImportSynchronizer):
    _model_name = ['magento.product.pricelist']

    @property
    def mapper(self):
       if self._mapper is None:
           self._mapper = self.get_connector_unit_for_model(PricelistImportMapper)
       return self._mapper

    def _must_skip(self):
        """ Hook called right after we read the data from the backend.

        If the method returns a message giving a reason for the
        skipping, the import will be interrupted and the message
        recorded in the job (if the import is called directly by the
        job, not by dependencies).

        If it returns None, the import will continue normally.

        :returns: None | str | unicode
        """
        if self.magento_record['type'] == 'configurable':
            return _('The configurable product is not imported in OpenERP, '
                     'because only the simple products are used in the sales '
                     'orders.')
        elif self.magento_record['type'] in ('virtual', 'grouped', 'bundle'):
            return _('Virtual, grouped and bundled products are not currently supported')


    def _create(self, data):
        raise NotImplementedError('Unable to create product when updating price lists. Please import products first.')

    def _update(self, binding_id, data):
        store_view_obj = self.session.pool.get('magento.storeview')
        store_view_id = self.session.context.get('store_view_id')
        store_view = store_view_obj.browse(self.session.cr, self.session.uid, store_view_id, context=self.session.context)
        pricelist = store_view.pricelist_id
        version = pricelist.version_id and pricelist.version_id[0].id or False
        if not version:
            version_obj = self.session.pool.get('product.pricelist.version')
            version_values = {
                    'name':(pricelist.name or '') + '_version',
                    'active': True,
                    'pricelist_id':pricelist.id,
                            }
            version = version_obj.create(self.session.cr, self.session.uid, version_values, context=self.session.context)

        product_binder_obj = self.session.pool.get('magento.product.product')
        product_binder = product_binder_obj.browse(self.session.cr, self.session.uid, binding_id, self.session.context)
        pricelist_item_obj = self.session.pool.get('product.pricelist.item')
        pricelist_item_ids = pricelist_item_obj.search(self.session.cr, 
                                                       self.session.uid, 
                                                       [('price_version_id', '=', version), 
                                                            ('product_id', '=', product_binder.openerp_id.id)], 
                                                        context=self.session.context)
        if not pricelist_item_ids:
            item_values = {
                'price_discount':-1,
                'price_surcharge':data.get('list_price',0.0),
                'price_version_id':version,
                'product_id':product_binder.openerp_id.id,
                }
            pricelist_item_ids = pricelist_item_obj.create(self.session.cr, self.session.uid, item_values, context=self.session.context)
        else:
            item_values = {
                'price_discount':-1,
                'price_surcharge':data.get('list_price',0.0),
                'price_round': 0.0,
                'price_min_margin': 0.0,
                'price_max_margin': 0.0,
                }
            pricelist_item_obj.write(self.session.cr, 
                                            self.session.uid, 
                                            pricelist_item_ids, 
                                            item_values, 
                                            context=self.session.context)
        return True

    def _get_binding_id(self):
        binder = self.get_binder_for_model('magento.product.product')
        return binder.to_openerp(self.magento_id)

    def _is_uptodate(self, binding_id):
        return False # Always force import

@magento
class PricelistDummyBinder(Binder):
    _model_name = [
            'magento.product.pricelist',
        ]

    def to_openerp(self, external_id, unwrap=False):
        raise NotImplementedError

    def to_backend(self, record_id, wrap=False):
        raise NotImplementedError

    def bind(self, external_id, binding_id):
        return True

@magento
class PricelistImportMapper(ImportMapper):
    _model_name = 'magento.product.pricelist'

    @mapping
    def price(self, record):
        """ The price is imported at the creation of
        the product, then it is only modified and exported
        from OpenERP """
        return {'list_price': record.get('price', 0.0)}

    @mapping
    def type(self, record):
        if record['type'] == 'simple':
            return {'type': 'product'}
        return {'type': record['type']}

    @mapping
    def website_ids(self, record):
        website_ids = []
        binder = self.get_binder_for_model('magento.website')
        for mag_website_id in record['websites']:
            website_id = binder.to_openerp(mag_website_id)
            website_ids.append((4, website_id))
        return {'website_ids': website_ids}

    @mapping
    def magento_id(self, record):
        return {'magento_id': record['product_id']}

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}

@job
@related_action(action=link)
def import_record(session, model_name, backend_id, magento_id, force=False, **kwargs):
    """ Import a record from Magento """
    env = get_environment(session, model_name, backend_id)
    importer = env.get_connector_unit(PricelistImport)
    importer.run(magento_id, force=force, **kwargs)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: