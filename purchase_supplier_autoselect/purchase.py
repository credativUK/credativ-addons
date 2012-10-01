# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2012 credativ Ltd (<http://credativ.co.uk>).
#    All Rights Reserved
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
import re

class purchase_order(osv.osv):
    _inherit = 'purchase.order'
    
    def onchange_name(self, cr, uid, ids, name):
        if name and name[:2] == 'PO': # Ignore default sequence
            return {}
        user = self.pool.get('res.users').browse(cr, uid, uid)
        
        try:
            supplier_code_regex = re.compile(user.company_id.po_name_regex or '(?<=^.{2}).{3}')
            supplier_code = supplier_code_regex.findall(name)
        except:
            supplier_code = []
        
        if not supplier_code or not supplier_code[0]:
            return {'warning': {'title': _('Warning!'), 'message': _('The PO name format does not match the format in the company configuration. Supplier must be selected manually.')}}
        
        supplier_ids = self.pool.get('res.partner').search(cr, uid, [('supplier', '=', True), ('ref', '=', supplier_code[0])])
        if supplier_ids and supplier_ids[0]:
            return {'value': {'partner_id': supplier_ids[0]}}
        else:
            return {'warning': {'title': _('Warning!'), 'message': _('The PO name containing supplier reference %s cannot be match to a known supplier. Supplier must be selected manually.' % (supplier_code[0], ))}}
        

purchase_order()

class purchase_order_line(osv.osv):
    _inherit = 'purchase.order.line'
    
    _columns = {
        'list_all_products': fields.boolean('List all Products', help='By default the products available will only be ones available from the selected supplier. This option will show all products available instead.'),
    }

purchase_order_line()
