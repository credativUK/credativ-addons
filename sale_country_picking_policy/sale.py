# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 credativ Ltd (<http://credativ.co.uk>).
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

from osv import osv, fields

class SaleOrder(osv.osv):
    _inherit = 'sale.order'

    def onchange_address_id(self, cr, uid, ids, partner_invoice_id,
                            partner_shipping_id, partner_id,
                            shop_id=False, context=None, **kwargs):

        res = super(SaleOrder, self).onchange_address_id(cr, uid, ids, partner_invoice_id,
                                        partner_shipping_id, partner_id,
                                        shop_id=shop_id, context=context, **kwargs)
        if partner_shipping_id:
            part = self.pool.get('res.partner').browse(cr, uid, partner_shipping_id, context=context)
            picking_policy = part.country_id and part.country_id.property_picking_policy
            if picking_policy:
                res['value'].update({'picking_policy': picking_policy})
        return res

    def onchange_workflow_process_id(self, cr, uid, ids, workflow_process_id,
                                     context=None, **kwargs):
        res = super(SaleOrder, self).onchange_workflow_process_id(cr, uid, ids,
                                        workflow_process_id, context=context, **kwargs)
        if res.get('value', {}).get('picking_policy'):
            del res['value']['picking_policy']
        return res

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
