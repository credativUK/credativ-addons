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

from openerp import models, fields, api

class ResPartner(models.Model):
    _inherit = 'res.partner'

    credit = fields.Float(compute='_credit_debit_get')
    debit = fields.Float(compute='_credit_debit_get')

    @api.multi
    def _credit_debit_get(self):
        sale_obj = self.env['sale.order']

        def amount_not_invoiced(order):
            order_currency = order.currency_id
            company_currency = order.company_id.currency_id

            invoices = order.invoice_ids
            invoices &= invoices.search([('state', 'not in', ['draft', 'cancel'])])

            invoiced = sum(invoices.mapped('amount_total'))

            return order_currency.compute(order.amount_total - invoiced, company_currency)

        # old API expects more arguments that we ever receive
        res = super(ResPartner, self)._credit_debit_get(['debit','credit'], None)

        for partner in self:
            orders = sale_obj.search([
                                      ('partner_id', 'child_of', partner.id),
                                      ('state', 'not in', ['draft', 'sent', 'cancel']),
                                      ('invoiced', '=', False),
                                     ])
            uninvoiced_total = sum(amount_not_invoiced(order) for order in orders)

            partner.credit = res[partner.id]['credit'] + uninvoiced_total
            partner.debit = res[partner.id]['debit']

        return res
