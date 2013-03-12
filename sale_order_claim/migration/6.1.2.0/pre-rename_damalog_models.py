# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2013 credativ Ltd (<http://credativ.co.uk>).
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

""" 2.0: Altered module name from sale_damagelog to sale_order_claim """

__name__ = """Alters the installed sale_damagelog module and its
models to reflect the new names used in sale_order_claim"""

import pooler
import logging
_logger = logging.getLogger('sale_order_claim migration')
_logger.setLevel(logging.DEBUG)

# TODO make this a module init function (or however that actually works)

def migrate(cr, version):
    return True # This migration is unlikely to work; we'll probably remove it eventually
    uid = 1

    if version == '6.1.2.0':
        # change name of sale_damagelog module
        modules_obj = pooler.get_pool(cr.dbname).get('ir.module.module')
        damagelog_mods = modules_obj.search(cr, uid, [('name','like','%damagelog%')], context=None)
        for mod_id in damagelog_mods:
            _logger.debug("""UPDATE ir_module_module SET name='sale_order_claim' WHERE id=%s""" % (mod_id,))
            cr.execute("""UPDATE ir_module_module SET name='sale_order_claim' WHERE id=%s""", (mod_id,))

        # change the module dependencies
        mdeps_obj = pooler.get_pool(cr.dbname).get('ir.module.module.dependency')
        damagelog_deps = mdeps_obj.search(cr, uid, [('name','like','%damagelog%')], context=None)
        for dep_id in damagelog_deps:
            _logger.debug("""UPDATE ir_module_module_dependency SET name='sale_order_claim' WHERE id=%s""" % (dep_id,))
            cr.execute("""UPDATE ir_module_module_dependency SET name='sale_order_claim' WHERE id=%s""", (dep_id,))

        # change the model names

        # TODO Do we actually need to do this? The old models can
        # safely be left

        # migrate data from old models to new
    else:
        _logger.debug('Migration does not apply to version %s' % (version,))
        
