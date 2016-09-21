# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright 2016 credativ Ltd
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

import ir_rule
import sys
import openerp
from openerp.tools.translate import _

fvg_orig = openerp.osv.orm.BaseModel.fields_view_get
ed_orig = openerp.osv.orm.BaseModel.export_data

def fields_view_get(self, cr, user, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
    res = fvg_orig(self, cr, user, view_id=view_id, view_type=view_type, context=context, toolbar=toolbar, submenu=submenu)
    try:
        self.pool.get('ir.model.access').check(cr, user, self._name, 'export')
    except openerp.osv.orm.except_orm as e:
        if e.name == 'Access Denied':
            if res.get('__action_permissions_extra') is None:
                res.update({'__action_permissions_extra': {}})
            res.get('__action_permissions_extra').update({'export':False})
    return res

def export_data(self, cr, uid, ids, fields_to_export, context=None):
    domain = self.pool.get('ir.rule')._compute_domain(cr, uid, self._name, 'export')
    ids_allowed = self.search(cr, uid, [('id','in',ids)] + domain, context=context)
    ids_disallowed = set(ids).difference(ids_allowed)
    if ids_disallowed:
        ids_disallowed_str = '\n'.join([str(id) for id in list(ids_disallowed)])
        raise openerp.osv.osv.except_osv(
                  _('Access Denied'),
                  _('No permission to access the following ids:\n\n%s' % ids_disallowed_str)
              )
    res = ed_orig(self, cr, uid, ids, fields_to_export, context=context)
    return res

def post_load():
    global fvg_orig
    global ed_orig
    sys.modules['openerp.addons.base'].ir.ir_rule.ir_rule._MODES.append('export')
    openerp.osv.orm.BaseModel.fields_view_get = fields_view_get
    openerp.osv.orm.BaseModel.export_data = export_data

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
