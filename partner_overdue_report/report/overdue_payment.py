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

import time

from report import report_sxw
import pooler

class overdue_payment(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(overdue_payment, self).__init__(cr, uid, name, context=context)
        self.localcontext.update( {
            'time': time,
            'adr_get': self._adr_get,
            'getLines': self._lines_get,
            'message': self._message,
        })
        self.context = context
    def _adr_get(self, partner, type):
        res = []
        res_partner = pooler.get_pool(self.cr.dbname).get('res.partner')
        res_partner_address = pooler.get_pool(self.cr.dbname).get('res.partner.address')
        
        addresses = res_partner.address_get(self.cr, self.uid, [partner], [type])
        adr_id = addresses and addresses[type] or False
        result = {
                  'name': False,
                  'street': False,
                  'street2': False,
                  'city': False,
                  'zip': False,
                  'state_id':False,
                  'country_id': False,
                  'vat': False,
                  'ref': False,
                 }
        if adr_id:
            result = res_partner_address.read(self.cr, self.uid, [adr_id], context=self.context.copy())[0]
            result['country_id'] = result['country_id'] and result['country_id'][1] or False
            result['state_id'] = result['state_id'] and result['state_id'][1] or False
        p = res_partner.browse(self.cr, self.uid, partner)
        result.update({'name' : p.name or '', 'vat':p.vat or False, 'ref': p.ref or False})
        
        res.append(result)
        return res

    def _lines_get(self, data, partner):
        moveline_obj = self.pool.get('account.move.line')
        movelines = moveline_obj.search(self.cr, self.uid,
                [('partner_id', '=', partner), ('move_id.date', '>=', data['date_from']), ('move_id.date', '<=', data['date_to']),
                    ('account_id.type', 'in', ['receivable', 'payable']),
                    ('state', '<>', 'draft'), ('reconcile_id', '=', False)])
        if movelines:
            movelines = moveline_obj.browse(self.cr, self.uid, movelines)
        return movelines

    def _message(self, partner):
        company = self.pool.get('res.partner').browse(self.cr, self.uid, partner).company_id
        return company and company.overdue_msg or ''

report_sxw.report_sxw('report.overdue.payment', 'res.partner',
        'addons/partner_overdue_report/report/overdue_payment.rml', parser=overdue_payment)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: