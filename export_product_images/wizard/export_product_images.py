# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 credativ Ltd (<http://credativ.co.uk>).
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

from openerp.osv import fields, osv
from openerp.tools.translate import _
import os
import base64

class export_product_images(osv.osv_memory):
    _name = "export.product.images"
    _description = "Save Product Image to a Particular Folder"

    _columns = {
        'location': fields.char('Location', help='Path to Save the Product Images'),
        'image_size': fields.selection([('image','Large'), ('image_medium','Medium'), ('image_small','Small')], 'Image Size', help=" Large Image is Limited to Maximum 1024x1024px, Medium is a 128x128px image and Small is a 64x64px image"),
    }
    _defaults = {
        'image_size': 'image'
    }
    
    def export_images(self, cr, uid, ids, context=None):
        product_obj = self.pool.get('product.template')
        if context is None: 
            context = {}
        current = self.browse(cr, uid, ids[0], context=context)
        product_ids = context.get('active_ids') or []
        
        if not os.path.exists(current.location):
            raise osv.except_osv(_('Error!'), _("Specified Location %s does not Exist.") % (current.location))
        elif not os.path.isdir(current.location):
            raise osv.except_osv(_('Error!'), _("Specified Location %s is not a Directory.") % (current.location))  
        elif not os.access(current.location, os.W_OK):
            raise osv.except_osv(_('Error!'), _("Specified Location %s does not have Write Access.") % (current.location)) 
            
        for product in product_obj.browse(cr, uid, product_ids, context=context):
            img = current.image_size == 'image' and product.image or (current.image_size == 'image_medium' and product.image_medium or product.image_small )
            product_img = base64.decodestring(str(img))
            file_name = (product.default_code and (product.default_code + "_") or "") + product.name.replace(' ','_') + '.jpg'
            fp = open(os.path.join(current.location, file_name.replace('/',' ')), 'w')
            fp.write(product_img)
            fp.close()   

        return True

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
