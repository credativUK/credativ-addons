# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution   
#    Copyright (C) 2015 credativ ltd (<http://www.credativ.co.uk>). All Rights Reserved
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

from openerp import models

class stock_picking(models.Model):
    _inherit = 'stock.picking'

    def do_copy_country_attachments(self, cr, uid, ids, context=None):
        '''This function copies attachments from the destination country to the picking'''
        context = dict(context or {})
        attachment_pool = self.pool.get('ir.attachment')
        for picking in self.browse(cr, uid, ids, context=context):
            country_id = picking.partner_id.country_id.id
            country_attachments = attachment_pool.search(cr ,uid, [('res_model','=','res.country'),('res_id','=',country_id)], context=context)
            for attachment in attachment_pool.browse(cr, uid, country_attachments, context=context):
                attachment.copy(default={'name':attachment.name, 'res_model':'stock.picking', 'res_id':picking.id})
        return True

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
