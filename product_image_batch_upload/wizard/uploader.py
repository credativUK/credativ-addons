import os
from osv import osv, fields
from osv.osv import except_osv
from tools.translate import _

try:
    import cStringIO as StringIO
except ImportError:
    import StringIO

from zipfile import ZipFile
from base64 import b64encode, b64decode



# Wizard which allows the user to upload a zipfile of images and writes
# them to products whose default_code (SKU) matches the filename.
class product_image_uploader(osv.TransientModel):
    _name = 'product_image_batch_upload.uploader'


    _columns = {
            'zipfile' : fields.binary('Zip File'),
    }


    # Returns a dicstionary which maps filenames to Odoo IDs.
    # Also performs validation.
    def _build_id_map(self, cr, uid, filenames, context=None):
        prod_obj = self.pool.get('product.product')
        missing_prods = []
        id_map = {}

        for filename in filenames:
            name = os.path.splitext(filename)[0]
            matches = prod_obj.search(cr, uid, [('default_code','=',name)], context=context)
            if not matches:
                missing_prods.append(name)
            else:
                id_map[filename] = matches[:]
        if missing_prods:
            raise except_osv(
                                _('Error: Unknown product'),
                                _('Products could not be found for the following SKUs:\n' + \
                                    '\n'.join(missing_prods)
                                )
                            )
        return id_map


    # Writes images stored in zipfile to objects specified in id_map
    def _write_images(self, cr, uid, id_map, zipfile, context=None):
        prod_obj = self.pool.get('product.product')
        for name in zipfile.namelist():
            ids = id_map.get(name)
            if ids:
                img_b64enc = b64encode(zipfile.open(name).read())
                prod_obj.write(cr, uid, ids, {'image' : img_b64enc}, context=context)


    # Apply images in uploaded zipfile to products.
    def upload(self, cr, uid, ids, context=None):
        self_browse = self.browse(cr, uid, ids[0], context=context)
        zip_str = StringIO(b64decode(self_browse.zipfile))
        zf = ZipFile(zip_str, 'a')

        id_map = self._build_id_map(cr, uid, zf.namelist(), context=context)
        self._write_images(cr, uid, id_map, zf, context=context)
        return {}



product_image_uploader()
