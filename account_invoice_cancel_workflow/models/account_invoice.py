# -*- coding: utf-8 -*-
# See __openerp__.py file in addon root folder for license details

from openerp.osv import orm

class AccountInvoice(orm.Model):
    _inherit = 'account.invoice'

    def action_cancel(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'workflow_process_id': False}, context=context)
        return super(AccountInvoice, self).action_cancel(cr, uid, ids, context=context)
