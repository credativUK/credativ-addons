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

import logging

from openerp.osv import fields,osv
from openerp.osv.orm import except_orm, browse_record
from openerp.tools.translate import _
from openerp import tools

_logger = logging.getLogger(__name__)

class ir_rule(osv.osv):
    _inherit = 'ir.rule'

    _columns = {
        'perm_export': fields.boolean('Apply for Export'),
    }

    _defaults = {
        'perm_export': True,
    }

    _sql_constraints = [
        ('no_access_rights', 'CHECK (perm_read!=False or perm_write!=False or perm_create!=False or perm_unlink!=False or perm_export!=False)', 'Rule must have at least one checked access right !'),
    ]

class ir_model_access(osv.osv):
    _inherit = 'ir.model.access'

    _columns = {
        'perm_export': fields.boolean('Export Access'),
    }

    def group_names_with_export(self, cr, model_name, access_mode):
        cr.execute('''SELECT
                        c.name, g.name
                      FROM
                        ir_model_access a
                        JOIN ir_model m ON (a.model_id=m.id)
                        JOIN res_groups g ON (a.group_id=g.id)
                        LEFT JOIN ir_module_category c ON (c.id=g.category_id)
                      WHERE
                        m.model=%s AND
                        a.active IS True AND
                        a.perm_export''', (model_name,))
        return [('%s/%s' % x) if x[0] else x[1] for x in cr.fetchall()]

    @tools.ormcache()
    def check(self, cr, uid, model, mode='read', raise_exception=True, context=None):
        try:
            # Passing args as keywords fails as the ormcache doesn't allow for it.
            # It should be safe to pass all args positionally by the same logic.
            return super(ir_model_access, self).check(cr, uid, model, mode, raise_exception, context)
        except AssertionError:
            if mode != 'export':
                raise

        if isinstance(model, browse_record):
            assert model._table_name == 'ir.model', 'Invalid model object'
            model_name = model.model
        else:
            model_name = model

        # TransientModel records have no access rights, only an implicit access rule
        if not self.pool.get(model_name):
            _logger.error('Missing model %s' % (model_name, ))
        elif self.pool.get(model_name).is_transient():
            return True

        # We check if a specific rule exists
        cr.execute('SELECT MAX(CASE WHEN perm_' + mode + ' THEN 1 ELSE 0 END) '
                   '  FROM ir_model_access a '
                   '  JOIN ir_model m ON (m.id = a.model_id) '
                   '  JOIN res_groups_users_rel gu ON (gu.gid = a.group_id) '
                   ' WHERE m.model = %s '
                   '   AND gu.uid = %s '
                   '   AND a.active IS True '
                   , (model_name, uid,)
                   )
        r = cr.fetchone()[0]

        if r is None:
            # there is no specific rule. We check the generic rule
            cr.execute('SELECT MAX(CASE WHEN perm_' + mode + ' THEN 1 ELSE 0 END) '
                       '  FROM ir_model_access a '
                       '  JOIN ir_model m ON (m.id = a.model_id) '
                       ' WHERE a.group_id IS NULL '
                       '   AND m.model = %s '
                       '   AND a.active IS True '
                       , (model_name,)
                       )
            r = cr.fetchone()[0]

        if not r and raise_exception:
            groups = '\n\t'.join('- %s' % g for g in self.group_names_with_export(cr, model_name, mode))
            msg_heads = {
                # Messages are declared in extenso so they are properly exported in translation terms
                'export': _("Sorry, you are not allowed to export this document."),
            }
            if groups:
                msg_tail = _("Only users with the following access level are currently allowed to do that") + ":\n%s\n\n(" + _("Document model") + ": %s)"
                msg_params = (groups, model_name)
            else:
                msg_tail = _("Please contact your system administrator if you think this is an error.") + "\n\n(" + _("Document model") + ": %s)"
                msg_params = (model_name,)
            _logger.warning('Access Denied by ACLs for operation: %s, uid: %s, model: %s', mode, uid, model_name)
            msg = '%s %s' % (msg_heads[mode], msg_tail)
            raise except_orm(_('Access Denied'), msg % msg_params)
        return r or False

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
