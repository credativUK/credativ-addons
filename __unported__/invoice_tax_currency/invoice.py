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
##############################################################################

from osv import osv, fields

class account_invoice_line(osv.osv):
    _inherit = 'account.invoice.line'

    def move_line_get(self, cr, uid, invoice_id, context=None):

        context = context or {}
        res = super(account_invoice_line,self).move_line_get(cr, uid, invoice_id, context=context)
        cur_obj = self.pool.get('res.currency')
        inv = self.pool.get('account.invoice').browse(cr, uid, invoice_id, context=context)
        company_currency = inv.company_id.currency_id
        #Change tax amount to invoice currency
        for vals in res:
            vals['tax_amount'] = cur_obj.compute(cr, uid, company_currency.id,inv.currency_id.id, vals.get('tax_amount', 0), context={'date': inv.date_invoice})
        return res

account_invoice_line()

class account_invoice_tax(osv.osv):
    _inherit = 'account.invoice.tax'

    def amount_change(self, cr, uid, ids, amount, currency_id=False, company_id=False, date_invoice=False):
        '''Update Tax amount '''

        cur_obj = self.pool.get('res.currency')
        res = super(account_invoice_tax,self).amount_change(cr, uid, ids, amount, currency_id, company_id, date_invoice)
        factor = 1
        if ids:
            factor = self.read(cr, uid, ids[0], ['factor_tax'])['factor_tax']
        if currency_id:
            currency = cur_obj.browse(cr, uid, currency_id)
            amount = cur_obj.round(cr, uid, currency, amount*factor)
            res['value']['tax_amount'] = amount
        return res

    def compute(self, cr, uid, invoice_id, context=None):
        '''Compute tax base and tax amount '''

        tax_obj = self.pool.get('account.tax')
        inv = self.pool.get('account.invoice').browse(cr, uid, invoice_id, context=context)
        res = super(account_invoice_tax,self).compute(cr, uid, invoice_id, context)
        #update base values with calculated values
        for key in res:
            tax = tax_obj.search(cr,uid,[('name','=',res[key]['name'])])
            if len(tax) > 1:
                #Narrow down search criteria on based on company
                tax = tax_obj.search(cr,uid,[('name','=',res[key]['name']),('company_id','=',inv.company_id.id)])
            if tax and tax_obj.browse(cr,uid,tax[0]).enable_invoice_entry:
                res[key]['base_amount'] = res[key]['base_amount'] > 0 and res[key]['base'] or (res[key]['base'] * -1)
                res[key]['tax_amount'] = res[key]['tax_amount'] > 0 and res[key]['amount'] or (res[key]['amount'] * -1)
        return res

account_invoice_tax()

class account_tax(osv.osv):

    _inherit = 'account.tax'
    
    _columns = {
        'enable_invoice_entry': fields.boolean('Use Currency Amount', help='Check if you wish this tax to be calculated using currency amount instead of amounting company currency.'),
        }

account_tax()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
