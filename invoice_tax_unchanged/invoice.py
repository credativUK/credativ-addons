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

class account_invoice_line(osv.osv):
    _inherit = 'account.invoice.line'
    
    def onchange_account_id(self, cr, uid, ids, fposition_id, account_id, invoice_line_tax_id=False):
        result = super(account_invoice_line, self).onchange_account_id(cr, uid, ids, fposition_id, account_id)
        unique_tax_ids = set(invoice_line_tax_id[0][2])
        if result and 'value' in result and 'invoice_line_tax_id' in result['value']:
            unique_tax_ids |= set(result['value']['invoice_line_tax_id'])
            
        return {'value':{'invoice_line_tax_id': list(unique_tax_ids)}}
    
account_invoice_line()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: