# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2014 credativ Ltd (<http://credativ.co.uk>).
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

class ResCompany(osv.Model):
    _inherit = 'res.company'

    def scheduler_send_invoice_notification(self, cr, uid, context=None):
        ids = self.search(cr, uid, [], context=context)
        model, res_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'account_invoice_notify', 'ir_actions_server_invoice_notify')
        for id in ids:
            ctx = {
                    'active_id': id,
                    'active_model': 'res.company',
            }
            self.pool.get('ir.actions.server').run(cr, uid, [res_id], ctx)

class AccountInvoice(osv.Model):
    _inherit = 'account.invoice'

    def send_invoice_notification(self, cr, uid, ids, user_id, context=None):
        model, res_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'account_invoice_notify', 'email_template_invoice_notify')
        invoices = self.browse(cr, uid, ids, context=context)
        mail_id = self.pool.get('email.template').send_mail(cr, uid, res_id, user_id, context={'invoices': invoices,})
        return mail_id

class AccountInvoiceWizardNotify(osv.TransientModel):
    _name = "account.invoice.wizard_notify"
    _description = "Send Invoice Notifications"
    _columns = {}

    def send(self, cr, uid, ids, context=None):
        model, res_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'account_invoice_notify', 'ir_actions_server_invoice_notify')
        act_obj = self.pool.get('ir.actions.server')
        company_invoice_dict = {}

        rec_ids = context and context.get('active_ids', False)
        assert rec_ids, _('Active IDs is not set in Context')

        for invoice in self.pool.get('account.invoice').browse(cr, uid, rec_ids, context=context):
            company_invoice_dict.setdefault(invoice.company_id.id, []).append(invoice)

        for company_id, invoices in company_invoice_dict.iteritems():
            user_ids = list(set([inv.user_id.id for inv in invoices]))
            states = list(set([inv.state for inv in invoices]))
            types = list(set([inv.type for inv in invoices]))
            ctx = {
                    'active_id': company_id,
                    'active_model': 'res.company',
                    '_invoice_ids': [inv.id for inv in invoices],
                    '_user_ids': user_ids,
                    '_invoice_types': types,
                    '_invoice_states': states,
                }
            act_obj.run(cr, uid, [res_id], ctx)

        return {'type': 'ir.actions.act_window_close'}
