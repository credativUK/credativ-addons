# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution    
#    Copyright (C) 2009 credativ Ltd (<http://credativ.co.uk>).
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

    _columns = {
        'name': fields.char('Name of Template Fragment', size=100, required=True),
        'for_template': fields.many2one('poweremail.templates', 'Email Template'),
        'model_id': fields.many2one('ir.model', 'Model', required=True),
        'template_language': fields.selection(template.TEMPLATE_ENGINES, 'Templating Language', required=True),
        'fragments_lines_ids': fields.one2many('poweremail.template_fragments_lines', 'template_fragment', string="Fragments Lines")
        }
    
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
            if line.res_id != 0 and line.template_fragment:
                res[line.id] = self.pool.get(line.template_fragment.model_id.model).browse(cr, uid, line.res_id, context=context).name 
        return res
        
    _columns = {
        'template_fragment': fields.many2one('poweremail.template_fragments', 'Template Fragment'),
        'res_id': fields.integer('Resource'),
        'name': fields.function(_get_resource_name, type='char', size=128, string='Resource Name', store=True),
        'lang': fields.many2one('res.lang', 'Language'),
        'body': fields.text('Fragment Content'),
        'partner_id': fields.many2one('res.partner', 'Partner', ondelete='cascade'),
        }
    
    def _get_lang(self, cr, uid, context=None):
        if context is None:
            context = {}
        user_lang = self.pool.get('res.users').browse(cr, uid, uid, context=context).context_lang
        lang_ids = self.pool.get('res.lang').search(cr, uid, [('code','=', user_lang)], context=context)
        return lang_ids and lang_ids[0] or False
    
    _defaults = {
        'lang': _get_lang,
        'res_id': 0
    }
    
    def _check_resource_exists(self, cr, uid, ids, context=None):
        for l in self.browse(cr, uid, ids, context=context):
            if not l.template_fragment:
                raise osv.except_osv(_('No fragment found !'), _('Save the Fragment.'))
            
            if l.res_id != 0:
                resources = self.pool.get(l.template_fragment.model_id.model).search(cr, uid, [('id','=',l.res_id)], context=context)
                if not resources:
                    return False
        return True
    
    _constraints = [
        (_check_resource_exists, 'Resource ID doesn\'t exist!', ['res_id']),
    ]
    
    def default_get(self, cr, uid, fields, context=None):
        data = super(poweremail_template_fragments_lines, self).default_get(cr, uid, fields, context=context)
        if context.get('default_record_id', False):
            data.update({'res_id': context['default_record_id']})
        return data
    
    def render_message(self, template_name, object, env):
        fragment = self.search(env['ctx']['cursor'], env['ctx']['uid'], [('template_fragment.name','=',template_name),('res_id','=',env['ctx']['carrier'].id)], context=env['ctx'])
        message = ''
        #If no fragment found for a carrier, then use the default one.
        if not fragment:
            fragment = self.search(env['ctx']['cursor'], env['ctx']['uid'], [('template_fragment.name','=',template_name),('res_id','=',0)], context=env['ctx'])
        if fragment:
            message = self.browse(env['ctx']['cursor'], env['ctx']['uid'], fragment[0], context=env['ctx']).body
        message = tools.ustr(message)
        return MakoTemplate(message).render_unicode(object=object,
                                                             peobject=object,
                                                             env=env,
                                                             format_exceptions=True)

poweremail_template_fragments_lines()

class poweremail_templates(osv.osv):
    _inherit = 'poweremail.templates'

    def generate_mail(self, cursor, user, template_id, record_ids, context=None):
        context.update({'fragment_function': self.pool.get('poweremail.template_fragments_lines').render_message, 'cursor': cursor})
        return super(poweremail_templates, self).generate_mail(cursor, user, template_id, record_ids, context=context)
    
poweremail_templates()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: