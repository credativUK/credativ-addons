# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution	
#    Copyright (C) 2013 credativ ltd (<http://www.credativ.co.uk>). All Rights Reserved
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

from osv import orm, expression, osv, fields
from openerp.tools.translate import _
import tools
from openerp import SUPERUSER_ID
import time
import logging
import traceback
_logger = logging.getLogger(__name__)

class ir_validation(osv.osv):
    _name = 'ir.validation'
    _order = 'name'
    _MODES = ['pre_write', 'post_write', 'post_create', 'pre_unlink']

    def _eval_context_for_combinations(self):
        return {'user': unquote('user'),
                'time': unquote('time')}

    def _eval_context(self, cr, uid):
        return {'user': self.pool.get('res.users').browse(cr, 1, uid),
                'time':time}

    def _domain_force_get(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        eval_context = self._eval_context(cr, uid)
        for rule in self.browse(cr, uid, ids, context):
            if rule.domain_force:
                res[rule.id] = expression.normalize(eval(rule.domain_force, eval_context))
            else:
                res[rule.id] = []
        return res

    def _get_value(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for rule in self.browse(cr, uid, ids, context):
            if not rule.groups:
                res[rule.id] = True
            else:
                res[rule.id] = False
        return res

    def _check_model_obj(self, cr, uid, ids, context=None):
        return not any(self.pool.get(rule.model_id.model).is_transient() for rule in self.browse(cr, uid, ids, context))

    def _check_model_name(self, cr, uid, ids, context=None):
        # Don't allow rules on rules records (this model).
        return not any((rule.model_id.model == self._name or rule.model_id.model == 'ir.rule') for rule in self.browse(cr, uid, ids, context))

    _columns = {
        'name': fields.char('Name', size=128, select=1),
        'model_id': fields.many2one('ir.model', 'Object',select=1, required=True, ondelete="cascade"),
        'global': fields.function(_get_value, string='Global', type='boolean', store=True, help="If no group is specified the rule is global and applied to everyone"),
        'groups': fields.many2many('res.groups', 'rule_group_rel', 'rule_group_id', 'group_id', 'Groups'),
        'domain_force': fields.text('Domain'),
        'domain': fields.function(_domain_force_get, string='Domain', type='text'),
        'message': fields.text('Validation Message', help="The message shown to the user on a failed validation", required=True),
        'perm_pre_write': fields.boolean('Apply For Pre-Write'),
        'perm_post_write': fields.boolean('Apply For Post-Write'),
        'perm_post_create': fields.boolean('Apply For Post-Create'),
        'perm_pre_unlink': fields.boolean('Apply For Pre-Delete'),
        'active': fields.boolean('Active'),
    }

    _order = 'model_id DESC'

    _defaults = {
        'perm_pre_write': True,
        'perm_post_write': True,
        'perm_post_create': True,
        'perm_pre_unlink': True,
        'global': True,
        'active': True,
    }
    _sql_constraints = [
        ('no_access_rights', 'CHECK (perm_pre_write!=False or perm_post_write!=False or perm_post_create!=False or perm_pre_unlink!=False)', 'Rule must have at least one checked access right !'),
    ]
    _constraints = [
        (_check_model_obj, 'Rules can not be applied on Transient models.', ['model_id']),
        (_check_model_name, 'Rules can not be applied on the Record Rules model or Validation model.', ['model_id']),
    ]

    @tools.ormcache()
    def _compute_domain(self, cr, uid, model_name, mode="pre_write"):
        if mode not in self._MODES:
            raise ValueError('Invalid mode: %r' % (mode,))

        cr.execute("""SELECT r.id
                FROM ir_validation r
                JOIN ir_model m ON (r.model_id = m.id)
                WHERE m.model = %s
                AND r.active = True
                AND r.perm_""" + mode + """
                AND (r.id IN (SELECT rule_group_id FROM rule_group_rel g_rel
                            JOIN res_groups_users_rel u_rel ON (g_rel.group_id = u_rel.gid)
                            WHERE u_rel.uid = %s) OR r.global)""", (model_name, uid))
        rule_ids = [x[0] for x in cr.fetchall()]
        if rule_ids:
            # browse user as super-admin root to avoid access errors!
            user = self.pool.get('res.users').browse(cr, SUPERUSER_ID, uid)
            global_domains = []                 # list of domains
            group_domains = {}                  # map: group -> list of domains
            messages = []
            for rule in self.browse(cr, SUPERUSER_ID, rule_ids):
                # read 'domain' as UID to have the correct eval context for the rule.
                rule_data = self.read(cr, uid, rule.id, ['domain', 'message'])
                rule_domain = rule_data['domain']
                messages.append(rule_data['message'])
                dom = expression.normalize(rule_domain)
                for group in rule.groups:
                    if group in user.groups_id:
                        group_domains.setdefault(group, []).append(dom)
                if not rule.groups:
                    global_domains.append(dom)
            # combine global domains and group domains
            if group_domains:
                group_domain = expression.OR(map(expression.OR, group_domains.values()))
            else:
                group_domain = []
            domain = expression.AND(global_domains + [group_domain])
            return domain, messages
        return [], []

    def _compute_domain_ittr(self, cr, uid, model_name, mode="pre_write"):
        if mode not in self._MODES:
            raise ValueError('Invalid mode: %r' % (mode,))

        cr.execute("""SELECT r.id
                FROM ir_validation r
                JOIN ir_model m ON (r.model_id = m.id)
                WHERE m.model = %s
                AND r.active = True
                AND r.perm_""" + mode + """
                AND (r.id IN (SELECT rule_group_id FROM rule_group_rel g_rel
                            JOIN res_groups_users_rel u_rel ON (g_rel.group_id = u_rel.gid)
                            WHERE u_rel.uid = %s) OR r.global)""", (model_name, uid))
        rule_ids = [x[0] for x in cr.fetchall()]
        if rule_ids:
            # browse user as super-admin root to avoid access errors!
            user = self.pool.get('res.users').browse(cr, SUPERUSER_ID, uid)
            for rule in self.browse(cr, SUPERUSER_ID, rule_ids):
                global_domains = []                 # list of domains
                group_domains = {}                  # map: group -> list of domains
                # read 'domain' as UID to have the correct eval context for the rule.
                rule_data = self.read(cr, uid, rule.id, ['domain', 'message'])
                rule_domain = rule_data['domain']
                message = rule_data['message']
                dom = expression.normalize(rule_domain)
                for group in rule.groups:
                    if group in user.groups_id:
                        group_domains.setdefault(group, []).append(dom)
                if not rule.groups:
                    global_domains.append(dom)
                # combine global domains and group domains
                if group_domains:
                    group_domain = expression.OR(map(expression.OR, group_domains.values()))
                else:
                    group_domain = []
                domain = expression.AND(global_domains + [group_domain])
                yield domain, message
        return

    def clear_cache(self, cr, uid):
        self._compute_domain.clear_cache(self)

    def domain_get(self, cr, uid, model_name, mode='read', context=None):
        try:
            dom, msg = self._compute_domain(cr, uid, model_name, mode)
            if dom:
                # _where_calc is called as superuser. This means that rules can
                # involve objects on which the real uid has no acces rights.
                # This means also there is no implicit restriction (e.g. an object
                # references another object the user can't see).
                query = self.pool.get(model_name)._where_calc(cr, 1, dom, active_test=False, context=context)
                return query.where_clause, query.where_clause_params, query.tables, msg
        except Exception, e:
            _logger.error('Error when processing validation rules. %s' % (traceback.format_exc(),))
            raise orm.except_orm(_('Validation Error'), _('Validation Error.\nError when processing validation rules:\n\n%s') % (e,))
        return [], [], ['"'+self.pool.get(model_name)._table+'"'], []

    def domain_get_ittr(self, cr, uid, model_name, mode='read', context=None):
        try:
            for dom, msg in self._compute_domain_ittr(cr, uid, model_name, mode):
                if dom:
                    # _where_calc is called as superuser. This means that rules can
                    # involve objects on which the real uid has no acces rights.
                    # This means also there is no implicit restriction (e.g. an object
                    # references another object the user can't see).
                    query = self.pool.get(model_name)._where_calc(cr, 1, dom, active_test=False, context=context)
                    yield query.where_clause, query.where_clause_params, query.tables, msg
        except Exception, e:
            _logger.error('Error when processing validation rules. %s' % (traceback.format_exc(),))
            raise orm.except_orm(_('Validation Error'), _('Validation Error.\nError when processing validation rules:\n\n%s') % (e,))
        return

    def unlink(self, cr, uid, ids, context=None):
        res = super(ir_validation, self).unlink(cr, uid, ids, context=context)
        self.clear_cache(cr, uid)
        return res

    def create(self, cr, uid, vals, context=None):
        res = super(ir_validation, self).create(cr, uid, vals, context=context)
        self.clear_cache(cr, uid)
        return res

    def write(self, cr, uid, ids, vals, context=None):
        res = super(ir_validation, self).write(cr, uid, ids, vals, context=context)
        self.clear_cache(cr,uid)
        return res

ir_validation()

def check_validation_rule(self, cr, uid, ids, opp, context=None):
    if context == None:
        context = {}
    if context.get('skip_validation', False):
        return
    where_clause, where_params, tables, msg = self.pool.get('ir.validation').domain_get(cr, uid, self._name, opp, context=context)
    if where_clause:
        where_clause = ' and ' + ' and '.join(where_clause)
        for sub_ids in cr.split_for_in_conditions(ids):
            cr.execute('SELECT ' + self._table + '.id FROM ' + ','.join(tables) + ' WHERE ' + self._table + '.id IN %s' + where_clause, [sub_ids] + where_params)
            if cr.rowcount != len(sub_ids): # We failed validation so now find which message(s) we need to show
                msgs = {}
                for where_clause, where_params, tables, msg in self.pool.get('ir.validation').domain_get_ittr(cr, uid, self._name, opp, context=context):
                    if where_clause:
                        where_clause = ' and ' + ' and '.join(where_clause)
                        for id in ids:
                            rec = repr(self.name_get(cr, uid, id, context=context))
                            cr.execute('SELECT ' + self._table + '.id FROM ' + ','.join(tables) + ' WHERE ' + self._table + '.id IN %s' + where_clause, [(id,)] + where_params)
                            if cr.rowcount != 1:
                                msgs.setdefault(rec, []).append(msg)
                error_strs = []
                for m_rec, m_msg in msgs.iteritems():
                    error_strs.append("%s:\n%s" % (m_rec, '\n'.join(m_msg)))
                error_str = "\n\n".join(error_strs)
                raise orm.except_orm(_('Validation Error'), _('Validation Error (Operation: %s, Document type: %s).\n\n%s') % (opp, self._description, error_str))
    return

def check_access_rule(self, cr, uid, ids, operation, context=None):
    res = self.check_access_rule_old(cr, uid, ids, operation, context=context)
    if operation in ('unlink', 'write', 'create'):
        opp = 'pre_write'
        if operation == 'unlink':
            opp = 'pre_unlink'
        if operation == 'create':
            opp = 'post_create'
        self.check_validation_rule(cr, uid, ids, opp, context=context)
    return res

def _validate(self, cr, uid, ids, context=None):
    res = self._validate_old(cr, uid, ids, context=context)
    self.check_validation_rule(cr, uid, ids, 'post_write', context=context)
    return res

orm.BaseModel.check_access_rule_old = orm.BaseModel.check_access_rule
orm.BaseModel._validate_old = orm.BaseModel._validate
orm.BaseModel.check_validation_rule = check_validation_rule

class ir_module_module(osv.osv):
    _inherit = 'ir.module.module'

    def check(self, cr, uid, ids, context=None):
        # Why this function..? Probably best not to ask, but this is the only function which is always called
        # at the end of every module being loaded so we can override functions of the base class consistantly
        if orm.BaseModel.check_access_rule.__code__ != orm.BaseModel.check_access_rule_old.__code__ and orm.BaseModel.check_access_rule.__code__ != check_access_rule.__code__:
            orm.BaseModel.check_access_rule_old = orm.BaseModel.check_access_rule
        if orm.BaseModel._validate.__code__ != orm.BaseModel._validate_old.__code__ and orm.BaseModel._validate.__code__ != _validate.__code__:
            orm.BaseModel._validate_old = orm.BaseModel._validate
        orm.BaseModel.check_access_rule = check_access_rule
        orm.BaseModel._validate = _validate
        res = super(ir_module_module, self).check(cr, uid, ids, context)

ir_module_module()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
