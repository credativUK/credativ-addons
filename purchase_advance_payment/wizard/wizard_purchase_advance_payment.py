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
import tools
from tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
from datetime import datetime

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
            'state': fields.selection([('advance', 'Advance Payment'), ('payment', 'Invoice Payment')], 'Payment Type', readonly=True),
        }

    def default_get(self, cr, uid, fields, context):
        rec_id = context and context.get('active_id', False)
        assert rec_id, _('Active ID is not set in Context')
        res = super(purchase_advance_payment, self).default_get(cr, uid, fields, context=context)

        purchase = self.pool.get('purchase.order').browse(cr, uid, rec_id, context=context)
        assert rec_id, _('Invalid PO ID')
        res['purchase_order_id'] = purchase.id
        res['partner_id'] = purchase.partner_id.id

        query = "select id from account_invoice where id in (select invoice_id from purchase_invoice_rel where purchase_id = %s) and state = 'open'"%(purchase.id)
        cr.execute(query)
        invoice_ids = tools.flatten(cr.fetchall())
        if not invoice_ids:
            state = 'advance'
        else:
            state = 'payment'
        res['state'] = state

        return res

    def onchange_amount(self, cr, uid, ids, amount, partner_id, purchase_order_id, journal_id, line_ids, state, context=None):
        if state == 'advance':
            ## FIXME: Currency conversion needed?
            #po = self.pool.get('purchase.order').browse(cr, uid, purchase_order_id, context=context)
            #if amount > po.amount_total:
            #    return {'value': {'amount': po.amount_total},
            #            'warning': {'title': 'Warning!', 'message': 'Cannot enter and amount greater than the PO total amount of %s' % (po.amount_total)}}
            return {'value': {}}

        res = {'value': {}}
        orig_amount = 0.0
        for line in line_ids:
            if line[0] == 4:
                raise osv.except_osv('Error !', 'Active ID is not set in Context. Please close and reload the wizard.')
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
            ## FIXME: Due to a bug in OpenERP 6.1 web client, it is not possible to update a one2many field
            ## from an edit of the same one2many field. It throws an error since the 'selected' field just edited
            ## is removed in the change but is still referenced. Maybe this will work in 7.0?
            if line[0] == 4:
                raise osv.except_osv('Error !', 'Active ID is not set in Context. Please close and reload the wizard.')
            if line[0] != 0:
            #    res_lines.append(line)
                continue
            data = line[2].copy()
            #if data.get('amount', 0.0) < 0.0:
            #    amount = 0.0
            #elif data.get('amount', 0.0) > data.get('amount_unreconciled', 0.0):
            #    amount = data.get('amount_unreconciled', 0.0)
            #else:
            #    amount = data.get('amount', 0.0)
            #data['amount'] = amount
            amount = data.get('amount', 0.0)
            running_amount += amount
            #res_lines.append([0, False, data])
        #res['value']['line_ids'] = res_lines
        res['value']['amount'] = running_amount
        return res

    def onchange_journal(self, cr, uid, ids, amount, partner_id, purchase_order_id, journal_id, line_ids, state, context=None):
        if state == 'advance':
            return

        aml_obj = self.pool.get('account.move.line')
        jor_pool = self.pool.get('account.journal')
        res = {'value': {}}
        res_lines = []
        currency_id = False
        if journal_id and jor_pool.browse(cr,uid,journal_id,context=context).currency:
            currency_id = jor_pool.browse(cr,uid,journal_id,context=context).currency.id
        lines = self.pool.get('account.voucher').recompute_voucher_lines(cr, uid, [], partner_id, journal_id, False, currency_id, 'payment', False)
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
        res_amount_update = self.onchange_amount(cr, uid, ids, amount, partner_id, purchase_order_id, journal_id, res_lines, state, context=context)
        res['value'].update(res_amount_update.get('value', {}))
        return res

    def advance_pay(self, cr, uid, ids, context=None):
        rec_id = context and context.get('active_id', False)
        if not rec_id:
            raise osv.except_osv('Error !', "Active ID is not set in Context. Please close and reload the wizard.")

        inv_obj = self.pool.get('account.invoice')
        ir_module_obj = self.pool.get('ir.module.module')
        seq_obj = self.pool.get('ir.sequence')
        move_obj = self.pool.get('account.move')
        currency_obj = self.pool.get('res.currency')

        data = self.browse(cr, uid, ids[0], context=context)

        if not data.amount or data.amount < 0:
            raise osv.except_osv('Error !', "Please enter an amount")

        ## FIXME: Currency conversion needed?
        #if data.amount > data.purchase_order_id.amount_total:
        #    raise osv.except_osv('Error !', "Amount must not be greater than the PO total amount of %s" % (data.purchase_order_id.amount_total))

        company = data.purchase_order_id.company_id
        partner = data.purchase_order_id.partner_id
        journal = data.journal_id
        period_pool = self.pool.get('account.period')
        type = 'in_invoice'
        currency_id = company.currency_id.id != journal.currency.id and journal.currency.id or False

        vals = inv_obj.onchange_partner_id(cr, uid, [], type, partner.id).get('value', {})
        src_account_id = vals.get('account_id', False)
        pay_account_id = journal.default_credit_account_id and journal.default_credit_account_id.id or False

        date = data.date or datetime.now().strftime(DEFAULT_SERVER_DATE_FORMAT)
        pids = period_pool.find(cr, uid, date, context=context)
        period_id = pids and pids[0] or False

        move_line_name = seq_obj.next_by_id(cr, uid, journal.sequence_id.id, context=context)
        move_name = seq_obj.next_by_id(cr, uid, journal.sequence_id.id, context=context)

        foreign_currency_diff = 0.0
        amount_currency = False
        if currency_id:
            amount_currency = currency_obj.compute(cr, uid, company.currency_id.id, currency_id, data.amount, context=context)

        move_lines = [[0,0,{
            'journal_id': journal.id,
            'period_id': period_id,
            'name': data.purchase_order_id.name,
            'account_id': src_account_id,
            'partner_id': partner.id,
            'currency_id': currency_id,
            'amount_currency': amount_currency,
            'quantity': 1,
            'debit': data.amount,
            'credit': 0.0,
            'date': date,
            'ref': move_name,
        }], [0,0,{
            'journal_id': journal.id,
            'period_id': period_id,
            'name': move_line_name,
            'account_id': pay_account_id,
            'amount_currency': -amount_currency,
            'partner_id': partner.id,
            'currency_id': currency_id,
            'quantity': 1,
            'credit': data.amount,
            'debit': 0.0,
            'date': date,
            'ref': move_name,
        }]]

        move = {
            'name': move_name,
            'journal_id': journal.id,
            'date': date,
            'period_id': period_id,
            'narration': data.name,
            'ref': data.reference or move_name,
            'purchase_order_id': data.purchase_order_id.id,
            'line_id': move_lines,
        }

        move_id = move_obj.create(cr, uid, move, context=context)

        return {'type': 'ir.actions.act_window_close'}


    def pay(self, cr, uid, ids, context=None):
        rec_id = context and context.get('active_id', False)
        if not rec_id:
            raise osv.except_osv('Error !', "Active ID is not set in Context. Please close and reload the wizard.")
        purchase_obj = self.pool.get('purchase.order')
        voucher_obj = self.pool.get('account.voucher')
        seq_obj = self.pool.get('ir.sequence')

        data = self.browse(cr, uid, ids[0], context=context)
        lines = []
        move_name = seq_obj.next_by_id(cr, uid, data.journal_id.sequence_id.id, context=context)
        for line in data.line_ids:
            if line.amount == 0:
                continue
            if line.amount < 0 or line.amount > line.amount_unreconciled:
                raise osv.except_osv('Error !', "Pay amount for each line must not exceed open balance")
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
                    'name': data.purchase_order_id.name,
                }])

        if not lines:
            raise osv.except_osv('Error !', "Please enter an amount for at least one open line")

        data = {
                'type': 'payment',
                'date': data.date or time.strftime('%Y-%m-%d'),
                'journal_id': data.journal_id.id,
                'amount': data.amount,
                'reference': data.reference,
                'partner_id': data.partner_id.id,
                'account_id': data.journal_id.default_credit_account_id and data.journal_id.default_credit_account_id.id or False,
                'company_id': self.pool.get('res.company')._company_default_get(cr, uid, 'account.voucher',context=context),
                'period_id': voucher_obj._get_period(cr, uid, context=context),
                'line_ids': lines,
                'reference': data.reference or data.purchase_order_id.name,
                'narration': data.name,
                'name': move_name,
            }
        vid = voucher_obj.create(cr, uid, data, context=context)
        return {
                'name': 'Supplier Payment',
                'view_type': 'form',
                'view_mode': 'form,tree',
                'res_model': 'account.voucher',
                'views': [(self.pool.get('ir.model.data').get_object_reference(cr, uid, 'account_voucher', 'view_vendor_payment_form')[1], 'form')],
                'res_id': vid,
                'type': 'ir.actions.act_window',
            }

    def pay_and_validate(self, cr, uid, ids, context=None):
        res = self.pay(cr, uid, ids, context=context)
        vid = res['res_id']
        self.pool.get('account.voucher').proforma_voucher(cr, uid, [vid,], context=context)
        return {'type': 'ir.actions.act_window_close'}

purchase_advance_payment()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
