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

from openerp.osv import orm, fields

class res_partner(orm.Model):
    _inherit = 'res.partner'

    _columns = {
            'property_payment_account': fields.property(
            'res.partner.bank',
            type='many2one',
            relation='res.partner.bank',
            string="Payment Account",
            view_load=True,
            domain="[('company_id','=',company_id)]" ,
            help="Bank account the customer should pay into")
    }

    def onchange_company_id(self, cr, uid, ids, company_id):
        property_obj = self.pool.get('ir.property')
        res = {}
        context = company_id and {'force_company': company_id} or {}
        acc = property_obj.get(cr, uid, 'property_payment_account', 'res.partner', context=context)
        if acc:
            res.setdefault('value', {}).update({'property_payment_account': acc.id})
        return res

    def create(self, cr, uid, vals, context=None):
        if not 'property_payment_account' in vals and vals.get('company_id'):
            property_obj = self.pool.get('ir.property')
            acc = property_obj.get(cr, uid, 'property_payment_account', 'res.partner', context={'force_company': vals.get('company_id')})
            if acc:
                vals.update({'property_payment_account': acc.id})
        return super(res_partner, self).create(cr, uid, vals, context)

class account_invoice(orm.Model):
    _inherit = 'account.invoice'

    _columns = {
            'payment_detail': fields.text('Additional payment details')
    }

    def create(self, cr, uid, vals, context=None):
        partner_id = vals.get('partner_id')
        if partner_id:
            partner = self.pool.get('res.partner').browse(cr, uid, partner_id).commercial_partner_id
            payment_account = False
            if partner.company_id.id:
                ctx = dict(context, force_company=partner.company_id.id, company_id=partner.company_id.id)
                payment_account = partner.property_payment_account or False
            vals.update({
                    'partner_bank_id': payment_account and payment_account.id or False,
                    'payment_detail': payment_account and payment_account.payment_detail or '',
                })
        return super(account_invoice, self).create(cr, uid, vals, context=context)

    def onchange_partner_id(self, cr, uid, ids, type, partner_id, date_invoice=False, payment_term=False, partner_bank_id=False, company_id=False):
        res = super(account_invoice, self).onchange_partner_id(cr, uid, ids, type, partner_id)
        if partner_id:
            partner = self.pool.get('res.partner').browse(cr, uid, partner_id).commercial_partner_id
            res.setdefault('domain', {})['partner_bank_id'] = [('company_id','=',partner.company_id.id)]
            res.setdefault('value', {}).update({
                    'partner_bank_id': partner.property_payment_account.id or False,
                    'payment_detail': partner.property_payment_account and partner.property_payment_account.payment_detail or '',
                })
        return res

class res_partner_bank(orm.Model):
    _inherit = 'res.partner.bank'

    _columns = {
            'payment_detail': fields.text('Additional payment details')
    }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
