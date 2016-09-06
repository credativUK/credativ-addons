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

from collections import defaultdict

from openerp import models, fields, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    credit = fields.Float(compute='_credit_debit_get')
    debit = fields.Float(compute='_credit_debit_get')

    @api.multi
    def _credit_debit_get(self):
        sale_obj = self.env['sale.order']
        invoice_obj = self.env['account.invoice']
        currency_obj = self.env['res.currency']

        # old API expects more arguments that we ever receive
        res = super(ResPartner, self)._credit_debit_get(['debit','credit'], None)

        for partner in self:
            order_domain = [
                ('partner_id', 'child_of', partner.id),
                ('state', 'not in', ['draft', 'sent', 'cancel']),
                ('invoiced', '=', False),
            ]

            uninvoiced_total = 0.0
            for group in sale_obj.read_group(order_domain,
                                             ['company_id'], ['company_id']):
                orders = sale_obj.search(group['__domain'])
                company_currency = orders[0].company_id.currency_id

                invoice_domain = [
                    ('state', 'not in', ['draft', 'cancel']),
                    ('sale_ids', 'in', list(orders._ids)),
                ]

                currency_total = defaultdict(lambda: 0.0)

                for order in orders:
                    currency_total[order.currency_id.id] += order.amount_total

                for invoice_data in invoice_obj.read_group(invoice_domain,
                                                           ['currency_id', 'amount_total'],
                                                           ['currency_id']):
                    currency_total[invoice_data['currency_id'][0]] -= invoice_data['amount_total']

                uninvoiced_total += sum(
                    currency_obj.browse(currency_id).compute(total, company_currency)
                    for currency_id, total
                    in currency_total.iteritems())

            partner.credit = res[partner.id]['credit'] + uninvoiced_total
            partner.debit = res[partner.id]['debit']

        return res
