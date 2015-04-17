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

    def onchange_partner_shipping_id(self, cr, uid, ids, part, context=None):
        res = {'value': {}}
        if part:
            part = self.pool.get('res.partner').browse(cr, uid, part, context=context)
            picking_policy = part.country_id and part.country_id.property_picking_policy
            if picking_policy:
                res['value'] = {'picking_policy': picking_policy}
        return res

    def onchange_partner_id(self, cr, uid, ids, part, context=None):
        res = super(SaleOrder, self).onchange_partner_id(cr, uid, ids, part, context=context)

        part_ship = res['value'].get('partner_shipping_id')
        if part_ship:
            res['value'].update(self.onchange_partner_shipping_id(cr, uid, ids, part_ship, context=context)['value'])

        return res

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
