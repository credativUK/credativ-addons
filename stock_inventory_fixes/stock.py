# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright 2014 credativ Ltd
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

from openerp.osv import osv

class stock_inventory(osv.osv):
    _inherit = "stock.inventory"

    def action_confirm(self, cr, uid, ids, context=None):
            """ override action_confirm to pass force_company in context
            @return: True
            """

            if context is None:
                context = {}
            for inventory in self.browse(cr, uid, ids, context=context):
                context_copy = context.copy()
                if 'force_company' not in context_copy and inventory.company_id:
                    context_copy['force_company'] = inventory.company_id.id
                super(stock_inventory,self).action_confirm(cr,uid,[inventory.id],context=context_copy)
            return True

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: