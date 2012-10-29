# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
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
from tools.translate import _

class account_invoice(osv.osv):
    _inherit = 'account.invoice'
    _columns = {
        'currency_id': fields.many2one('res.currency', 'Currency', required=True, readonly=True),
    }

account_invoice()

class account_change_currency(osv.osv_memory):
    _inherit = 'account.change.currency'
    
    def change_currency(self, cr, uid, ids, context=None):
        result = super(account_change_currency, self).change_currency(cr, uid, ids, context=context)

        obj_inv = self.pool.get('account.invoice')
        obj_inv_line = self.pool.get('account.invoice.line')
        obj_currency = self.pool.get('res.currency')
        if context is None:
            context = {}        
        
        #Calculation of unit price in change_currency() was incorrect. To rectify it, the following change was inevitable.
        invoice = obj_inv.browse(cr, uid, context['active_id'], context=context)
        for inv_line in invoice.invoice_line:
            res = obj_inv_line.product_id_change(cr, uid, [], inv_line.product_id.id, inv_line.product_id.uos_id.id, inv_line.quantity, inv_line.name, invoice.type, invoice.partner_id.id, invoice.fiscal_position and invoice.fiscal_position.id or False, inv_line.price_unit, invoice.address_invoice_id.id, invoice.currency_id.id, context=context.update({'company_id':invoice.company_id.id}))
            new_price = res['value']['price_unit'] * invoice.currency_id.rate
            obj_inv_line.write(cr, uid, [inv_line.id], {'price_unit': new_price}, context=context)
        
        #Compute Taxes button function is called so that user need not click on the button manually to get the correct value for the taxes.
        obj_inv.button_reset_taxes(cr, uid, [context['active_id']], context=context)
        return result
    
account_change_currency()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: