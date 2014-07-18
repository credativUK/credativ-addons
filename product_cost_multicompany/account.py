# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution   
#    Copyright (C) 2014 credativ ltd (<http://www.credativ.co.uk>). All Rights Reserved
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
from openerp.tools.translate import _

class AccountAnalyticLine(osv.Model):
    _inherit = 'account.analytic.line'

    def on_change_unit_amount(self, cr, uid, id, prod_id, quantity, company_id, unit=False, journal_id=False, context=None):
        context = context or {}
        res = super(AccountAnalyticLine, self).on_change_unit_amount(cr, uid, id, prod_id, quantity, company_id, unit=unit, journal_id=journal_id, context=context)

        ctx = context.copy()
        ctx['company_id'] = company_id
        if not journal_id:
            j_ids = self.pool.get('account.analytic.journal').search(cr, uid, [('type','=','purchase')])
            journal_id = j_ids and j_ids[0] or False
        if not journal_id or not prod_id:
            return {}
        product_obj = self.pool.get('product.product')
        analytic_journal_obj =self.pool.get('account.analytic.journal')
        product_price_type_obj = self.pool.get('product.price.type')
        uom_obj = self.pool.get('product.uom')
        j_id = analytic_journal_obj.browse(cr, uid, journal_id, context=ctx)
        prod = product_obj.browse(cr, uid, prod_id, context=ctx)
        result = 0.0
        if prod_id:
            unit = prod.uom_id.id
            if j_id.type == 'purchase':
                unit = prod.uom_po_id.id

        if journal_id:
            journal = analytic_journal_obj.browse(cr, uid, journal_id, context=ctx)
            if journal.type == 'sale':
                product_price_type_ids = product_price_type_obj.search(cr, uid, [('field','=','list_price')], context=ctx)
                if product_price_type_ids:
                    return res # If we are using list_price here, return

        amount_unit = prod.standard_price
        if unit:
            amount_unit = uom_obj._compute_price(cr, uid, unit, amount_unit)
        prec = self.pool.get('decimal.precision').precision_get(cr, uid, 'Account')
        amount = amount_unit * quantity or 0.0
        result = round(amount, prec)

        res.update({'amount': result})
        return res

class ResCurrency(osv.Model):
    _inherit = 'res.currency'

    def _get_conversion_rate(self, cr, uid, from_currency, to_currency, context=None):
        # If the companies don't match, the base currencies may also not match.
        # Change the from currency to the same company as the to currency by matching the currency names and company_id
        if to_currency.company_id.id != from_currency.company_id.id:
            new_from_currency_id = self.search(cr, uid, [('name', '=', from_currency.name), ('company_id', '=', to_currency.company_id.id)])
            if new_from_currency_id:
                from_currency = self.browse(cr, uid, new_from_currency_id)[0]
        return super(ResCurrency, self)._get_conversion_rate(cr, uid, from_currency, to_currency, context=context)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
