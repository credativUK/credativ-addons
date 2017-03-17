# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2017 credativ Ltd (<http://credativ.co.uk>).
#    All Rights Reserved
#    $Id$
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
from osv import fields, osv
from tools.translate import _

class service_quotation(osv.osv):
    _inherit = 'service.quotation'

    _columns = {

        'parent_id': fields.many2one(
            'service.quotation', 'Original Quote',
            help="Original Quote."),
        'revision_ids': fields.one2many(
            'service.quotation', 'parent_id', 'Revisions',
            readonly=True, states={'draft': [('readonly', False)]}, select=True,
            help="Revisions for the quote."),
        'state': fields.selection([
            ('draft', 'Draft'),
            ('preopen', 'Pre Open'),
            ('open', 'Open - Quote Not Yet Printed'),
            ('open_email', 'Open - Quote Not Yet Sent'),
            ('prenotif', 'Open - Quote To Be Faxed Now'),
            ('notif', 'Open - Quote To Be Faxed'),
            ('notif_email', 'Open - Quote To Be Emailed'),
            ('sent', 'Open - Quote Sent'),
            ('lost', 'Closed - Lost'),
            ('won', 'Closed - Won'),
            ('revised', 'Closed - Revised')
        ], 'State', select=True, readonly=True),

    }

    def action_won(self, cr, uid, ids):
        for quotation in self.browse(cr, uid, ids, context={}):
            if not quotation.parent_id:
                return super(service_quotation, self).action_won(cr, uid, ids)
            if quotation.parent_id and quotation.parent_id.state == 'won':
                raise osv.except_osv(_('sqq7: Error'),
                                     _('sqq7: Original quote is in won state kindly change the state to revised'))
            old_quotation = quotation.parent_id
            contract_id = old_quotation.contract_assignment_id.current_contract_id.id

            quotation.write({'contract_assignment_id': old_quotation.contract_assignment_id.id})
            self.pool.get('quotation.wizard').assign_new_prices(cr, uid, old_quotation, quotation, contract_id, old_quotation.contract_assignment_id)
            quotation.write({'state': 'won'})
        return True

    def action_revise(self, cr, uid, ids, context={}):
        for quotation in self.browse(cr, uid, ids):
            quotation.write({'state': 'revised'})
        return True

service_quotation()
