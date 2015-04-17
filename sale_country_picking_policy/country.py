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
from tools.translate import _

class ResCountry(osv.osv):
    _inherit = 'res.country'

    def _get_picking_policy(self, cr, uid, ids, name, arg, context=None):
        res = {}
        for record in self.browse(cr, uid, ids, context=context):
            res[record.id] = record.property_picking_policy or False
        return res

    def _save_picking_policy(self, cr, uid, id, name, value, args, context=None):
        return self.write(cr, uid, [id], {'property_picking_policy': value}, context=context)

    _columns = {
        'property_picking_policy': fields.property(
            'res.country',
            type='char',
            view_load=True,
            string='Shipping Policy'),
        'property_picking_policy_dummy': fields.function(
            _get_picking_policy, fnct_inv=_save_picking_policy,
            type='selection',
            selection=[('direct', 'Deliver each product when available'), ('one', 'Deliver all products at once')],
            string='Shipping Policy',
            help="If set the shipping policy on the country will override the default policy on the sale order"),
    }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
