# -*- coding: utf-8 -*-
# © 2016 credativ Ltd (http://credativ.co.uk)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, api


class AccountVoucher(models.Model):

    _inherit = "account.voucher"

    @api.multi
    def actionSendEmail(self):
        '''
        This function opens a window to compose an email
        '''

        self.ensure_one()
        try:
            template = self.env.ref('account_voucher_remittance_email.email_template_voucher_remittance')
            mail_wizard = self.env.ref('mail.email_compose_message_wizard_form')
        except ValueError as e:
            raise Exception(e.message)

        ctx = dict()
        ctx.update({
            'default_model': 'account.voucher',
            'default_res_id': self.ids[0],
            'default_use_template': bool(template.id),
            'default_template_id': template.id,
            'default_composition_mode': 'comment',
        })
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(mail_wizard.id, 'form')],
            'view_id': mail_wizard.id,
            'target': 'new',
            'context': ctx,
        }

    @api.multi
    def send_email(self):
        '''
        This function sends email to supplier
        '''
        return self.actionSendEmail()
