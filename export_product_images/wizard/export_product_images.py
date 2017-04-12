# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
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
import unicodedata
import shutil
from datetime import datetime
from tempfile import mkdtemp

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
        directory_obj = self.pool.get('document.directory')
        if context is None: 
            context = {}
        current = self.browse(cr, uid, ids[0], context=context)
        product_ids = context.get('active_ids') or []
        
        tmpdir = mkdtemp(suffix='',prefix='product_images_')
        
        direc_ids = directory_obj.search(cr, uid, [('name','=','Products')], context=context)
        
        #if not os.path.exists(current.location):
        #    raise osv.except_osv(_('Error!'), _("Specified Location %s does not Exist.") % (current.location))
        #elif not os.path.isdir(current.location):
        #    raise osv.except_osv(_('Error!'), _("Specified Location %s is not a Directory.") % (current.location))  
        #elif not os.access(current.location, os.W_OK):
        #    raise osv.except_osv(_('Error!'), _("Specified Location %s does not have Write Access.") % (current.location)) 
            
        for product in product_obj.browse(cr, uid, product_ids, context=context):
            img = current.image_size == 'image' and product.image or (current.image_size == 'image_medium' and product.image_medium or product.image_small )
            product_img = base64.decodestring(str(img))
            file_name = (product.default_code and (product.default_code + "_") or "") + product.name.replace(' ','_') + '.jpg'
            file_name = file_name.replace('/',' ')
            file_name = unicodedata.normalize('NFKD', file_name).encode('ascii','ignore')
            fp = open(os.path.join(tmpdir, file_name), 'w')
            fp.write(product_img)
            fp.close()  
                        
        name = 'Products Images ' + datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        shutil.make_archive(tmpdir, "zip", tmpdir)
        attachment_id = self.pool.get('ir.attachment').create(cr, uid, {
            'name':name,
            'res_name': name,
            'type': 'binary',
            'res_model': False, 
            'res_id': False,
            'datas': open(tmpdir+'.zip','rb').read().encode('base64'),
            'datas_fname': 'Products Images.zip',
            'parent_id':direc_ids and direc_ids[0] or False
            }, context=context)  
        shutil.rmtree(tmpdir)
        os.remove(tmpdir+'.zip')
        return True

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
