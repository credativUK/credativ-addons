# -*- coding: utf-8 -*-
from openerp import http
#from openerp.addons.base.ir import data

class WebRest(http.Controller):
     @http.route('/search/<string:model>/<int:id>', type="http", auth='public')
     def index(self, **kw):

        #menu_data = http.request.registry['ir.ui.menu'].load_menus(http.request.cr, http.request.uid, context=http.request.context)

#	ids = data.search(cr, uid, [('module','=','project.task'), ('name','=', 'Task')])

        #return http.request.render('project.task')

        #model = request.registry.get('ir.actions.act_window')
        #act_id = http.request.env['ir.actions.act_window'].search([('res_model', '=', kw['model']), ('context', '=', '{}')], limit=1).id
	#act_id = 149;

	result = http.request.cr.execute("""SELECT iaw.id "act_id", ium.id "menu_id" 
		FROM ir_act_window iaw 
		INNER JOIN ir_values iv 
			ON iv.value = 'ir.actions.act_window,' || iaw.id::VARCHAR 
			AND iv.model = 'ir.ui.menu'
		INNER JOIN ir_ui_menu ium
    			ON ium.id = iv.res_id
			WHERE iaw.res_model = %s
		ORDER BY ium.sequence ASC
		LIMIT 1;""", (str(kw['model']),))	
	
	result = http.request.cr.dictfetchall()[0]
	act_id = result['act_id']
	menu_id = result['menu_id']

	return http.local_redirect("/web/#id="+str(kw['id'])+"&view_type=form&model="+kw['model']+"&menu_id="+str(menu_id)+"&action="+str(act_id), query=http.request.params, keep_hash=True)
	#return http.local_redirect("/web/#id=13&view_type=form&model=project.task&menu_id=141&action=149") 
	


#     @http.route('/web_rest/web_rest/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('web_rest.listing', {
#             'root': '/web_rest/web_rest',
#             'objects': http.request.env['web_rest.web_rest'].search([]),
#         })

#     @http.route('/web_rest/web_rest/objects/<model("web_rest.web_rest"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('web_rest.object', {
#             'object': obj
#         })
