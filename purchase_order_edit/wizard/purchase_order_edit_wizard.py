# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution   
#    Copyright (C) 2015 credativ Ltd (<http://credativ.co.uk>).
#    All Rights Reserved
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

class PurchaseOrderEditWizard(osv.osv_memory):
    _name = "purchase.order.edit_wizard"
    _description = "Edit Order Items"
    _columns = {
        'purchase_order_id' : fields.many2one('purchase.order', required=True),
        }

    def default_get(self, cr, uid, fields, context):
        purchase_order_id = context and context.get('active_id', False) or False
        res = super(PurchaseOrderEditWizard, self).default_get(cr, uid, fields, context=context)
        res.update({'purchase_order_id': purchase_order_id or False})
        return res

    def edit_order(self, cr, uid, ids, context=None):
        purchase_obj = self.pool.get('purchase.order')

        for data in self.browse(cr, uid, ids, context=context):
            new_id = purchase_obj.copy_for_edit(cr, uid, data.purchase_order_id.id, context=context)

        return {
                'name': 'Edit Order',
                'view_type': 'form',
                'view_mode': 'form,tree',
                'res_model': 'purchase.order',
                'view_id': False,
                'res_id': new_id,
                'type': 'ir.actions.act_window',
            }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
