# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution    
#    Copyright (C) 2012 credativ Ltd (<http://credativ.co.uk>).
#    All Rights Reserved
#    $Id$
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
from osv import osv, fields
from poweremail import template
from urllib import quote as quote
from mako.template import Template as MakoTemplate
import tools

class poweremail_template_fragments(osv.osv):
    _name = 'poweremail.template_fragments'

    def onchange_model(self, cr, uid, ids, model_id, context=None):
        if model_id:
            model = self.pool.get('ir.model').read(cr, uid, model_id, ['model'])['model']
            return {'value': {'model_name': model, 'model_id': False}}
        return {}
    
    _columns = {
        'name': fields.char('Fragment Name', size=100, required=True),
        'model_id': fields.many2one('ir.model', 'Model (Change Only)', help="Use this field to find the string representation of the model, this field does not represent the model used."),
        'model_name': fields.char('Model', size=100, required=True, help="The string representation of the model this fragment relates to"),
        'template_language': fields.selection(template.TEMPLATE_ENGINES, 'Templating Language', required=True),
        'fragments_lines_ids': fields.one2many('poweremail.template_fragments_lines', 'template_fragment_id', string="Fragments Lines")
        }
    
    _sql_constraints = [
        ('name_uniq', 'UNIQUE(name)', 'A template fragment with this name already exists'),
    ]    
    
poweremail_template_fragments()
    
class poweremail_template_fragments_lines(osv.osv):
    _name = 'poweremail.template_fragments_lines'
    _rec_name = 'res_id'
    
    def _get_resource_name(self, cr, uid, ids, field_names, args, context=None):
        if not ids: return {}
        res = {}
        if context is None:
            context = {}
        for line in self.browse(cr, uid, ids, context=context):
            if line.res_id != 0:
                record = False
                model_pool = False
                if line.template_fragment_id.model_name:
                    model_pool = self.pool.get(line.template_fragment_id.model_name)
                if model_pool:
                    record = model_pool.read(cr, uid, line.res_id, ['name'], context=context)
                if record:
                    res[line.id] = record['name']
                else:
                    res[line.id] = "<NOT FOUND>"
            else:
                res[line.id] = "<DEFAULT>"
        return res
    
    def _get_fragment_ids(self, cr, uid, ids, context=None):
        res = set()
        for move in self.pool.get('poweremail.template_fragments').browse(cr, uid, ids, context):
            res.update([x.id for x in move.fragments_lines_ids])
        return list(res)
    
    def onchange_res_id(self, cr, uid, ids, res_id, model_name, context=None):
        if res_id == 0:
            return {'value': {'name': "<DEFAULT>"}}
        model_pool = False
        if model_name:
            model_pool = self.pool.get(model_name)
        if model_pool:
            record = model_pool.read(cr, uid, res_id, ['name'], context=context)
            if record:
                return {'value': {'name': record['name']}}
            else:
                return {'value': {'name': "<NOT FOUND>"}}
        else:
            return {'warning': {'title': 'Unable to find model', 'message': 'Model is either not set or is incorrect in the Template Fragment object'}}

    def onchange_fragment_id(self, cr, uid, ids, res_id, template_fragment_id, context=None):
        if template_fragment_id:
            template_fragment_id = self.pool.get('poweremail.template_fragments').browse(cr, uid, template_fragment_id, context=context)
        if template_fragment_id:
            return self.onchange_res_id(cr, uid, ids, res_id, template_fragment_id.model_name, context=context)
        else:
            return {'value': {'name': "<NOT FOUND>"}}
    
    _columns = {
        'template_fragment_id': fields.many2one('poweremail.template_fragments', 'Template Fragment', required=True),
        'res_id': fields.integer('Resource'),
        'model_name': fields.related('template_fragment_id', 'model_name', type='char', string='Model', readonly=True,
            store={
                'poweremail.template_fragments_lines': (lambda self, cr, uid, ids, ctx: ids, ['template_fragment_id'], 10),
                'poweremail.template_fragments': (_get_fragment_ids, ['model_name'], 20)
            }),
        'name': fields.function(_get_resource_name, type='char', size=128, string='Resource Name',
            store={
                'poweremail.template_fragments_lines': (lambda self, cr, uid, ids, ctx: ids, ['res_id', 'template_fragment_id'], 10),
                'poweremail.template_fragments': (_get_fragment_ids, ['model_name'], 20)
            }),
        'lang_id': fields.many2one('res.lang', 'Language', required=True),
        'body': fields.text('Fragment Content', required=True),
        }

    _sql_constraints = [
        ('res_id_uniq', 'UNIQUE(res_id, template_fragment_id, lang_id)', 'A template fragment line already exists for this template fragment, resource and language.'),
    ]    
    
    def _get_lang(self, cr, uid, context=None):
        if context is None:
            context = {}
        user_lang = self.pool.get('res.users').browse(cr, uid, uid, context=context).context_lang
        lang_ids = self.pool.get('res.lang').search(cr, uid, [('code','=', user_lang)], context=context)
        return lang_ids and lang_ids[0] or False
    
    _defaults = {
        'lang_id': _get_lang,
        'res_id': 0
    }
    
    _order = 'template_fragment_id asc, lang_id asc, res_id asc'
    
    def render_message(self, cr, uid, ids, template_name, res_id, object, env, lang=None, context=None):
        if ids:
            raise NotImplementedError("Ids is just there by convention! Don't use it yet, please.")
        fragment_obj = self.pool.get('poweremail.template_fragments')
        fragment_id = fragment_obj.search(cr, uid, [('name','=',template_name),], context=context)
        if fragment_id:
            fragment_id = fragment_obj.browse(cr, uid, fragment_id[0], context=context)
        else:
            raise osv.except_osv('Unable to render template fragment', "A template fragment with name '%s' cannot be found." % (template_name))
        fragment_line_id = self.search(cr, uid, [('template_fragment_id','=',fragment_id.id),('res_id','=',res_id),('lang_id.code','=',lang)], context=context)
        if not fragment_line_id:
            fragment_line_id = self.search(cr, uid, [('template_fragment_id','=',fragment_id.id),('res_id','=',0),('lang_id.code','=',lang)], context=context)
        if not fragment_line_id:
            res_name = self.onchange_res_id(cr, uid, [], res_id, fragment_id.model_name, context=None).get('value', {}).get('name', '<NOT FOUND>')
            raise osv.except_osv('Unable to render template fragment', "A template fragment line cannot be found for '%s', with language '%s', for resouce %d (%s) or default." % (fragment_id.name, lang, res_id, res_name))
        fragment_line_id = self.browse(cr, uid, fragment_line_id[0], context=context)
        if fragment_line_id.template_fragment_id.template_language == 'mako':
            try:
                return MakoTemplate(tools.ustr(fragment_line_id.body)).render_unicode(object=object, peobject=object, env=env, format_exceptions=True)
            except Exception, e:
                raise osv.except_osv('Unable to render template fragment', "There was an error processing template fragment '%s', with language '%s', for resouce %d (%s):\n%s." % (fragment_id.name, lang, fragment_line_id.res_id, fragment_line_id.name, e))
        else:
            raise NotImplementedError("Template lanugage '%s' not currently supported by poweremail_template_fragments." % (fragment_line_id.template_fragment_id.template_language))
 
    def render_message_wrapper(self, template_name, res_id, object, env, lang=None):
        context = env.get('ctx', {})
        cr = object._cr
        uid = object._uid
        if not lang:
            lang = context.get('lang')
        return self.render_message(cr, uid, [], template_name, res_id, object, env, lang=lang, context=context)
 
poweremail_template_fragments_lines()

class poweremail_templates(osv.osv):
    _inherit = 'poweremail.templates'

    def generate_mail(self, cursor, user, template_id, record_ids, context=None):
        if context is None:
            context = {}
        context.update({'frag_func': self.pool.get('poweremail.template_fragments_lines').render_message_wrapper})
        return super(poweremail_templates, self).generate_mail(cursor, user, template_id, record_ids, context=context)
    
poweremail_templates()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: