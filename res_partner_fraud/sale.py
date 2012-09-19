# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2012 credativ Ltd (<http://credativ.co.uk>).
#    All Rights Reserved
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

class sale_order(osv.osv):
    _inherit = 'sale.order'
    
    def _get_sale_from_partner(self, cr, uid, partner_ids, context=None):
        # Using pool.get instead of just self - possibly a core bug but self in this function is actualy res.partner!?
        sale_ids = self.pool.get('sale.order').search(cr, uid, [('partner_id', 'in', partner_ids),], context=context)
        return sale_ids
    
    _columns = {
        'flag_fraud': fields.related('partner_id', 'flag_fraud', string='Fraud', type='boolean',
                store={
                        'res.partner': (_get_sale_from_partner, ['flag_fraud'], 10),
                        'sale.order': (lambda self, cr, uid, ids, ctx: ids, ['partner_id'], 10),
                      },
                help='The partner associated with this sale has been flagged for fraud',
            ),
        }

sale_order()
