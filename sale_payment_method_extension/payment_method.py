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

from openerp.osv import fields, orm


class payment_method(orm.Model):
    _inherit = "payment.method"

    _columns = {
        'shop_id': fields.many2one('sale.shop',
                            'Shop',
                            domain="[('company_id','=',company_id)]",
                            help="Sale shop. Shop with selected company will\
                                            only appear in selection box.",
                            ),
    }

    _sql_constraints = [
        ('shop_company_uniq', 'unique (shop_id, company_id)',
            'The Shop on payment method must be unique per company!'),
    ]

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
