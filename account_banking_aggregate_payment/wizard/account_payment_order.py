# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#    Contributors: credativ ltd (<http://www.credativ.co.uk>).
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

import netsvc

from openerp.osv import fields, osv
from openerp.tools.translate import _
from collections import defaultdict
from openerp.osv import orm

class payment_order_create(osv.osv_memory):
    """
        Inherited from original class payment_order_create from account_payment
    """

    _inherit = 'payment.order.create'

    def getPartnerBank(self, cr, uid, ids, payment_mode_id=None, context=None):
        """
        Get partner bank
        Return the first suitable bank for the corresponding partner.
        """

        payment_mode_obj = self.pool.get('payment.mode')
        partner_obj = self.pool.get('res.partner')

        if not ids:
            return {}
        bankList = {}
        bank_type = payment_mode_obj.suitable_bank_types(cr, uid,
                                                         payment_mode_id,
                                                         context=context)
        for partner in partner_obj.browse(cr, uid, ids, context=context):
            bankList[partner.id] = False
            for bank in partner.bank_ids:
                if bank.state in bank_type:
                    bankList[partner.id] = bank.id
                else:
                    raise osv.except_osv(_('Error!'), _('There is no partner defined on the entry line.'))
        return bankList

    def create_payment(self, cr, uid, ids, context=None):
        """
            Group by payment lines on partner
        """

        order_obj = self.pool.get('payment.order')
        payment = order_obj.browse(cr, uid, context['active_id'],
                                            context=context)
        # Check for payment order aggregate
        if not (payment and payment.mode.aggregate):
            return super(payment_order_create, self).create_payment(cr,
                                                                    uid,
                                                                    ids,
                                                                    context)

        line_obj = self.pool.get('account.move.line')
        payment_obj = self.pool.get('payment.line')
        if context is None:
            context = {}
        data = self.browse(cr, uid, ids, context=context)[0]
        line_ids = [entry.id for entry in data.entries]
        if not line_ids:
            return {'type': 'ir.actions.act_window_close'}

        payment = order_obj.browse(cr, uid, context['active_id'],
                                            context=context)

        aggregateLines = defaultdict(dict)
        aggregateLines.default_factory = lambda:{'line_ids':[], 'amount':0}
        # TODO Implement payment due date
        if payment.date_prefered == 'fixed':
            date_to_pay = payment.date_scheduled
        else:
            date_to_pay = False

        ## Finally populate the current payment with new lines:
        for line in line_obj.browse(cr, uid, line_ids, context=context):
            aggregateLines[line.partner_id.id]['amount'] += line.amount_to_pay
            aggregateLines[line.partner_id.id]['line_ids'].append(line.id)

        #Create payment lines
        for partner_id,aggregateLine in aggregateLines.iteritems():
            line2bank = self.getPartnerBank(cr, uid, [partner_id],
                                                     payment.mode.id,
                                                     context=context)

            orderline_id = payment_obj.create(cr, uid, {
                #'move_line_id': line.id,
                'move_ids':[(6,0,aggregateLine['line_ids'])],
                'amount_currency': aggregateLine['amount'],
                'bank_id': line2bank[partner_id],
                'order_id': payment.id,
                'partner_id': partner_id,
                'communication': '/',
                'communication2': False,
                'state': 'structured',
                'date': date_to_pay,
                'currency': payment.mode.journal.currency and
                            payment.mode.journal.currency.id or
                            payment.mode.journal.company_id.currency_id.id
                }, context=context)

        return {
            'name': _('Payment Orders'),
            'context': context,
            'view_type': 'form',
            'view_mode': 'form,tree',
            'res_model': 'payment.order',
            'res_id': context['active_id'],
            'type': 'ir.actions.act_window',
        }

    def search_entries(self, cr, uid, ids, context=None):
        """
            Customer search for account move line entries.
        """
        line_obj = self.pool.get('account.move.line')
        mod_obj = self.pool.get('ir.model.data')
        if context is None:
            context = {}
        data = self.browse(cr, uid, ids, context=context)[0]
        search_due_date = data.duedate
        #payment = self.pool.get('payment.order').browse(cr, uid, context['active_id'], context=context)

        # Search for move line to pay:
        domain = [('reconcile_id', '=', False), ('account_id.type', '=', 'payable'), ('amount_to_pay', '>', 0)]
        domain = domain + ['|', ('date_maturity', '<=', search_due_date), ('date_maturity', '=', False)]
        line_ids = line_obj.search(cr, uid, domain, context=context)
        context.update({'line_ids': line_ids})
        model_data_ids = mod_obj.search(cr, uid,[('model', '=', 'ir.ui.view'), ('name', '=', 'view_create_payment_order_lines')], context=context)
        resource_id = mod_obj.read(cr, uid, model_data_ids, fields=['res_id'], context=context)[0]['res_id']
        return {'name': _('Entry Lines'),
                'context': context,
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'payment.order.create',
                'views': [(resource_id,'form')],
                'type': 'ir.actions.act_window',
                'target': 'new',
        }

payment_order_create()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
