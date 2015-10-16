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

from openerp import models, api, _

class stock_picking(models.Model):
    _inherit = 'stock.picking'

    @api.one
    def do_copy_country_attachments(self):
        '''This function copies attachments from the destination country to the picking'''
        attachmentObj = self.env['ir.attachment']
        country_id = self.partner_id.country_id.id
        country_attachments = attachmentObj.search([('res_model','=','res.country'),('res_id','=',country_id)])
        for attachment in country_attachments:
            attachment.copy(default={'name':attachment.name, 'res_model':'stock.picking', 'res_id':self.id})
        return True

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
