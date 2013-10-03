# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution    
#    Copyright (C) 2013 credativ Ltd (<http://credativ.co.uk>).
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

import netsvc
import time
from osv import osv, fields
import decimal_precision as dp
from tools.translate import _

class purchase_advance_payment_line(osv.osv_memory):
    _name = "purchase.advance.payment.line"

    def _compute_balance(self, cr, uid, ids, name, args, context=None):
        currency_pool = self.pool.get('res.currency')
        rs_data = {}
        for line in self.browse(cr, uid, ids, context=context):
            ctx = context.copy()
            ctx.update({'date': line.purchase_advance_payment_id.date})
            res = {}
            company_currency = line.purchase_advance_payment_id.journal_id.company_id.currency_id.id
            voucher_currency = company_currency
            move_line = line.move_line_id or False

            if not move_line:
                res['amount_original'] = 0.0
                res['amount_unreconciled'] = 0.0
            elif move_line.currency_id and voucher_currency==move_line.currency_id.id:
                res['amount_original'] = currency_pool.compute(cr, uid, move_line.currency_id.id, voucher_currency, abs(move_line.amount_currency), context=ctx)
                res['amount_unreconciled'] = currency_pool.compute(cr, uid, move_line.currency_id and move_line.currency_id.id or company_currency, voucher_currency, abs(move_line.amount_residual_currency), context=ctx)
            elif move_line and move_line.credit > 0:
                res['amount_original'] = currency_pool.compute(cr, uid, company_currency, voucher_currency, move_line.credit, context=ctx)
                res['amount_unreconciled'] = currency_pool.compute(cr, uid, company_currency, voucher_currency, abs(move_line.amount_residual), context=ctx)
            else:
                res['amount_original'] = currency_pool.compute(cr, uid, company_currency, voucher_currency, move_line.debit, context=ctx)
                res['amount_unreconciled'] = currency_pool.compute(cr, uid, company_currency, voucher_currency, abs(move_line.amount_residual), context=ctx)

            rs_data[line.id] = res
        return rs_data

    _columns = {
            'purchase_advance_payment_id' : fields.many2one('purchase.advance.payment', required=True,),
            'invoice_id' : fields.many2one('account.invoice', 'Invoice', readonly=True,),
            'move_line_id': fields.many2one('account.move.line', 'Journal Item', readonly=True,),
            'amount_original': fields.function(_compute_balance, multi='dc', type='float', string='Original Amount', store=True, digits_compute=dp.get_precision('Account'),),
            'amount_unreconciled': fields.function(_compute_balance, multi='dc', type='float', string='Open Balance', store=True, digits_compute=dp.get_precision('Account'), readonly=True,),
            'amount': fields.float('Amount', digits_compute=dp.get_precision('Account'),),
            'date_original': fields.related('move_line_id', 'date', type='date', string='Date', readonly=True,),
            'date_due': fields.related('move_line_id', 'date_maturity', type='date', string='Due Date', readonly=True,),
        }

purchase_advance_payment_line()

class purchase_advance_payment(osv.osv_memory):
    _name = "purchase.advance.payment"

    _columns = {
            'purchase_order_id': fields.many2one('purchase.order', readonly=True),
            'partner_id': fields.related('purchase_order_id', 'partner_id', type='many2one', relation='res.partner', string='Partner', readonly=True),
            'journal_id':fields.many2one('account.journal', 'Journal', required=True),
            'name':fields.char('Memo', size=256,),
            'date':fields.date('Date',),
            'line_ids':fields.one2many('purchase.advance.payment.line','purchase_advance_payment_id','Payment Lines',),
            'amount': fields.float('Total', digits_compute=dp.get_precision('Account'), required=True,),
            'reference': fields.char('Ref #', size=64,),
        }

    def default_get(self, cr, uid, fields, context):
        rec_id = context and context.get('active_id', False)
        assert rec_id, _('Active ID is not set in Context')
        res = super(purchase_advance_payment, self).default_get(cr, uid, fields, context=context)

        purchase = self.pool.get('purchase.order').browse(cr, uid, rec_id, context=context)
        assert rec_id, _('Invalid PO ID')
        res['purchase_order_id'] = purchase.id
        res['partner_id'] = purchase.partner_id.id

        return res

    def onchange_amount(self, cr, uid, ids, amount, partner_id, purchase_order_id, journal_id, line_ids, context=None):
        res = {'value': {}}
        orig_amount = 0.0
        for line in line_ids:
            if line[0] != 0:
                continue
            orig_amount += line[2].get('amount', 0.0)
        if orig_amount == amount:
            return {}

        running_amount = amount
        res_lines = []
        for line in line_ids:
            if line[0] != 0:
                res_lines.append(line)
                continue
            data = line[2].copy()
            if running_amount >= data.get('amount_unreconciled', 0.0):
                data['amount'] = data.get('amount_unreconciled', 0.0)
                running_amount -= data.get('amount_unreconciled', 0.0)
            else:
                data['amount'] = running_amount
                running_amount = 0.0
            res_lines.append([0, False, data])
        res['value']['line_ids'] = res_lines
        if running_amount > 0:
            res['value']['amount'] = amount - running_amount
        return res

    def onchange_line_ids(self, cr, uid, ids, amount, partner_id, purchase_order_id, journal_id, line_ids, context=None):
        res = {'value': {}}
        running_amount = 0.0
        res_lines = []
        for line in line_ids:
            if line[0] != 0:
                res_lines.append(line)
                continue
            data = line[2].copy()
            if data.get('amount', 0.0) < 0.0:
                amount = 0.0
            elif data.get('amount', 0.0) > data.get('amount_unreconciled', 0.0):
                amount = data.get('amount_unreconciled', 0.0)
            else:
                amount = data.get('amount', 0.0)
            data['amount'] = amount
            running_amount += amount
            res_lines.append([0, False, data])
        res['value']['line_ids'] = res_lines
        res['value']['amount'] = running_amount
        return res

    def onchange_journal(self, cr, uid, ids, amount, partner_id, purchase_order_id, journal_id, line_ids, context=None):
        aml_obj = self.pool.get('account.move.line')
        res = {'value': {}}
        res_lines = []
        lines = self.pool.get('account.voucher').recompute_voucher_lines(cr, uid, [], partner_id, journal_id, False, False, 'payment', False)
        for line in lines['value']['line_dr_ids']:
            ml = aml_obj.browse(cr, uid, line['move_line_id'], context=context)
            if ml.invoice and purchase_order_id in [x.id for x in ml.invoice.purchase_ids]:
                res_lines.append([0, False, {
                    'invoice_id': ml.invoice.id,
                    'move_line_id': ml.id,
                    'date_original': ml.date,
                    'date_due': ml.date_maturity,
                    'amount_original': line['amount_original'],
                    'amount_unreconciled': line['amount_unreconciled'],
                    }])
        res['value']['line_ids'] = res_lines
        res_amount_update = self.onchange_amount(cr, uid, ids, amount, partner_id, purchase_order_id, journal_id, res_lines, context=context)
        res['value'].update(res_amount_update.get('value', {}))
        return res

    def pay(self, cr, uid, ids, context=None):
        rec_id = context and context.get('active_id', False)
        assert rec_id, _('Active ID is not set in Context')
        purchase_obj = self.pool.get('purchase.order')
        voucher_obj = self.pool.get('account.voucher')

        data = self.browse(cr, uid, ids[0], context=context)
        lines = []
        for line in data.line_ids:
            lines.append([0, False, {
                    'account_id': data.partner_id.property_account_payable.id,
                    'amount': line.amount,
                    'reconcile': False,
                    'type': 'dr',
                    'move_line_id': line.move_line_id.id,
                    'date_original': line.date_original,
                    'date_due': line.date_due,
                    'amount_original': line.amount_original,
                    'amount_unreconciled': line.amount_unreconciled,
                }])

        data = {
                'type': 'payment',
                'date': data.date or time.strftime('%Y-%m-%d'),
                'journal_id': data.journal_id.id,
                'amount': data.amount,
                'reference': data.reference,
                'partner_id': data.partner_id.id,
                'account_id': data.partner_id.property_account_payable.id,
                'company_id': self.pool.get('res.company')._company_default_get(cr, uid, 'account.voucher',context=context),
                'period_id': voucher_obj._get_period(cr, uid, context=context),
                'line_ids': lines,
            }
        vid = voucher_obj.create(cr, uid, data, context=context)
        voucher_obj.proforma_voucher(cr, uid, [vid,], context=context)
        return {'type': 'ir.actions.act_window_close'}

purchase_advance_payment()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
