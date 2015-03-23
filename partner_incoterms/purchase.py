# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 credativ Ltd (<http://credativ.co.uk>).
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

from openerp import fields, models, api

class purchase_order(models.Model):
    _inherit = 'purchase.order'
    
    incoterm_id = fields.Many2one('stock.incoterms', 'Incoterm', states={'confirmed':[('readonly',True)], 'approved':[('readonly',True)],'done':[('readonly',True)]})
    
    def onchange_partner_id(self, cr, uid, ids, partner_id):
        res = super(purchase_order, self).onchange_partner_id(cr, uid, ids, partner_id)
        if partner_id:
            partner = self.pool.get('res.partner').browse(cr, uid, partner_id)
            if partner.default_incoterm_id:
                res['value']['incoterm_id'] = partner.default_incoterm_id.id
        return res

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
