# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 credativ Ltd (<http://www.credativ.co.uk>).
#    All Rights Reserved
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

from openerp.addons.connector.unit.mapper import (mapping,
                                                  ImportMapper
                                                  )

from openerp.addons.magentoerpconnect.backend import magento
from openerp.addons.magentoerpconnect import sale

@magento(replacing=sale.SaleOrderImportMapper)
class SaleOrderImportMapper(sale.SaleOrderImportMapper):
    _model_name = 'magento.sale.order'

    @mapping
    def payment(self, record):
        company_id = False
        if not self.session.context.get('company_id', False):
            binder = self.get_binder_for_model('magento.storeview')
            storeview_id = binder.to_openerp(record['store_id'])
            assert storeview_id is not None, 'cannot import sale orders Payment from non existing storeview'
            storeview = self.session.browse('magento.storeview', storeview_id)
            company_id = storeview.store_id.openerp_id.company_id or False
            if company_id:
                company_id = company_id.id
        method_ids = self.session.search('payment.method',
                                [['name', '=', record['payment']['method']],
                                ['company_id', '=', company_id],
                                ['shop_id','=',storeview.store_id.id],
                                ])
        assert method_ids, ("method %s should exist because the import fails "
                            "in SaleOrderImport._before_import when it is "
                            " missing" % record['payment']['method'])
        method_id = method_ids[0]
        return {'payment_method_id': method_id}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
