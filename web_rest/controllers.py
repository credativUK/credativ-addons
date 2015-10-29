# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 credativ Ltd (<http://credativ.co.uk>).
#    All Rights Reserved
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

from openerp import http


class WebRest(http.Controller):
    @http.route('/search/<string:model>/<int:id>', type="http", auth='public')
    def index(self, **kw):

        result = http.request.cr.execute("""
                SELECT iaw.id "act_id", ium.id "menu_id"
                FROM ir_act_window iaw
                INNER JOIN ir_values iv
                        ON iv.value = 'ir.actions.act_window,' ||
                            iaw.id::VARCHAR
                        AND iv.model = 'ir.ui.menu'
                INNER JOIN ir_ui_menu ium
                            ON ium.id = iv.res_id
                        WHERE iaw.res_model = %s
                ORDER BY ium.sequence ASC
                LIMIT 1;""", (str(kw['model']),))

        result = http.request.cr.dictfetchall()[0]
        act_id = result['act_id']
        menu_id = result['menu_id']

        if menu_id is None or act_id is None:
            return http.local_redirect("/web")

        base_url = "/web/#id={}&view_type=form&model={}&menu_id={}&action={}"
        redirect_url = base_url.format(kw['id'], kw['model'], menu_id, act_id)

        return http.local_redirect(redirect_url,
                                   query=http.request.params,
                                   keep_hash=True)
