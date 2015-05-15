# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2014 credativ Ltd (<http://credativ.co.uk>).
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


class sale_order(osv.osv):

    _name    = 'sale.order'
    _inherit = 'sale.order'


    def _get_section_id(self, cr, uid, part, context=None):
        partner_obj  = self.pool.get('res.partner')
        partner_data = partner_obj.read(cr, uid, part, ['section_id'], context=context)
        section_id = partner_data['section_id'] and partner_data['section_id'][0] or False
        return section_id


    def onchange_partner_id(self, cr, uid, ids, part, context=None):
        res = super(sale_order, self).onchange_partner_id(cr, uid, ids, part, context=context)
        val = res.get('value') or {}
        section_id = self._get_section_id(cr, uid, part, context=context)
        val.update({'section_id' : section_id})
        res.update({'value' : val})
        return res
        

    def default_get(self, cr, uid, fields, context=None):
        res = super(sale_order, self).default_get(cr, uid, fields, context=context)
        part = res.get('partner_id', False)
        if part:
            res.update({'section_id' : self._get_section_id(cr, uid, part, context=context)})
        return res



sale_order()
