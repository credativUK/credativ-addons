# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2016 credativ ltd (<http://www.credativ.co.uk>). All Rights Reserved
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

from openerp.osv import fields, orm
from openerp import netsvc

from openerp.addons.queue_tasks.queue_task import defer

class purchase_order(orm.Model):
    _inherit = 'purchase.order'

    @defer("Cancel Purchase Order")
    def purchase_cancel_defer(self, cr, uid, ids, context=None):
        if getattr(self, 'purchase_cancel'):
            return self.purchase_cancel(cr, uid, ids, context=context)
        else:
            wf_service = netsvc.LocalService("workflow")
            for id in ids:
                wf_service.trg_validate(uid, 'purchase.order', id, 'purchase_cancel', cr)
            return True

    @defer("Confirm Purchase Order")
    def purchase_confirm_defer(self, cr, uid, ids, context=None):
        wf_service = netsvc.LocalService("workflow")
        for id in ids:
            wf_service.trg_validate(uid, 'purchase.order', id, 'purchase_confirm', cr)
        return True
