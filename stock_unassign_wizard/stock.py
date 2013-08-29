# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution   
#    Copyright (C) 2013 credativ ltd (<http://www.credativ.co.uk>). All Rights Reserved
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

from osv import osv, fields
from tools.translate import _

class stock_picking(osv.osv):
    _inherit = 'stock.picking'

    def action_assign(self, cr, uid, ids, context=None):
        if context == None:
            context = {}
        res = super(stock_picking, self).action_assign(cr, uid, ids, context)
        if len(ids) == 1: # Checks to make sure we should show the wizard
            pick = self.browse(cr, uid, ids)[0]
            move_ids = [x.id for x in pick.move_lines if x.state == 'confirmed']
            if move_ids: # Some are still confirmed, generate and show the wizard
                if context.get('skip_stock_unassign_wizard', False):
                    return False
                mod_obj = self.pool.get('ir.model.data')
                wiz_obj = self.pool.get('stock.unassign.wizard')
                wiz_id = wiz_obj.create(cr, uid, {'picking_id': pick.id,}, context=context)
                model_data_ids = mod_obj.search(cr, uid, [('model', '=', 'ir.ui.view'), ('name', '=', 'view_stock_unassign_wizard')], context=context)
                resource_id = mod_obj.read(cr, uid, model_data_ids, fields=['res_id'], context=context)[0]['res_id']
                return {
                    'name': _('Stock Unassign Wizard'),
                    'res_id': wiz_id,
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'stock.unassign.wizard',
                    'view_id': False,
                    'target': 'new',
                    'views': [(resource_id, 'form')],
                    'context': context,
                    'type': 'ir.actions.act_window',
                }
        return res

stock_picking()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
