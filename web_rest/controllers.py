# -*- coding: utf-8 -*-
from openerp import http
#from openerp.addons.base.ir import data

class WebRest(http.Controller):
     @http.route('/search/<string:model>/<int:id>', type="http", auth='public')
     def index(self, **kw):

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

	if menu_id == None or act_id == None:
		return http.local_redirect("/web") 

	return http.local_redirect("/web/#id="+str(kw['id'])+"&view_type=form&model="+kw['model']+"&menu_id="+str(menu_id)+"&action="+str(act_id), query=http.request.params, keep_hash=True)
