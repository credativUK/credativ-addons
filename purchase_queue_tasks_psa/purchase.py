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

class purchase_order(orm.Model):
    _inherit = 'purchase.order'

    _columns = {
            'procurements_auto_allocate_orig': fields.boolean('Auto Allocate Procurements - Origional Value'),
        }

    _defaults = {
            'procurements_auto_allocate_orig': False,
        }

    def _update_auto_state(self, cr, uid, ids, context=None):
        ''' Set the procurements_auto_allocate_orig flag to True if procurements_auto_allocate is True 
            It is left as is if already True and procurements_auto_allocate is now False as this could
            indicate the job is being queued twice '''
        update_ids = self.search(cr, uid, [('procurements_auto_allocate', '=', True), ('id', 'in', ids)], context=context)
        self.write(cr, uid, update_ids, {'procurements_auto_allocate_orig': True, 'procurements_auto_allocate': False}, context=context)
        return True

    def _restore_auto_state(self, cr, uid, ids, context=None):
        ''' Set the procurements_auto_allocate flag back to the origional value in procurements_auto_allocate_orig
            and reset this back to False. We should never see the case where procurements_auto_allocate is True
            and procurements_auto_allocate_orig is False, if we do then this is being run outside of a job and
            should be ignored '''
        update_ids = self.search(cr, uid, [('procurements_auto_allocate_orig', '=', True), ('id', 'in', ids)], context=context)
        self.write(cr, uid, update_ids, {'procurements_auto_allocate': True, 'procurements_auto_allocate_orig': False}, context=context)
        return True

class procurement_order(orm.Model):
    _inherit = 'procurement.order'

    def _planned_purchases_get_purchases(self, cr, uid, procurement, po_ids, context=None):
        res = super(procurement_order, self)._planned_purchases_get_purchases(cr, uid, procurement, po_ids, context=context)
        purchase_ids = self.pool.get('purchase.order').search(cr, uid, [('id', 'in', res), ('procurements_auto_allocate', '=', True)], context=context)
        return purchase_ids

class queue_task(orm.Model):
    _inherit = 'queue.task'

    def queue_task(self, cr, uid, ids, context=None):
        for job in self.browse(cr, uid, ids, context=context):
            if job.model == 'purchase.order':
                self.pool.get('purchase.order')._update_auto_state(cr, uid, [job.res_id], context=context)
        return super(queue_task, self).queue_task(cr, uid, ids, context=context)

    def run_task(self, cr, uid, ids, context=None):
        for job in self.browse(cr, uid, ids, context=context):
            if job.model == 'purchase.order':
                self.pool.get('purchase.order')._restore_auto_state(cr, uid, [job.res_id], context=context)
        return super(queue_task, self).run_task(cr, uid, ids, context=context)
