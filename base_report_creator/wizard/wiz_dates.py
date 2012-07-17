# -*- coding: utf-8 -*-
##############################################################################
#    
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2012 credativ (<http://www.credativ.co.uk>).
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

from osv import fields, osv

class date_wizard(osv.osv_memory):
    _name = "base_report_creator.date_wizard"
    _description = "Enter Dates for Report"
    _columns = {
        'from_menu':fields.boolean('From a menu item?'),
        'from_date':fields.date('Date From', required=True),
        'to_date':fields.date('Date To', required=True),
    }
    _defaults = {
        'from_menu': False,
    }
    
    def report_run(self, cr, uid, ids, context=None):
        data = self.browse(cr, uid, ids, context=context)
        report_id = context.get('report_id', False)
        obj_board = self.pool.get('base_report_creator.report')
        data_obj = self.pool.get('ir.model.data')
        result = {}
        
        if report_id:
            board = obj_board.browse(cr, uid, report_id, context=context)
            view = board.view_type1
            if board.view_type2:
                view += ',' + board.view_type2
            if board.view_type3:
                view += ',' + board.view_type3
            result = data_obj._get_id(cr, uid, 'base_report_creator', 'view_report_filter')
            res = data_obj.read(cr, uid, result, ['res_id'])
            
            result = {
                'name': board.name,
                'view_type': 'form',
                'view_mode': view,
                'res_model': 'base_report_creator_report.result',
                'search_view_id': res['res_id'],
                'type': 'ir.actions.act_window',
            }
            
        if result and data and data[0].from_date and data[0].to_date and context.get('report_id', False):
            result['context'] = repr({
                    'report_id': board.id,
                    'dates': {
                                'from_date': data[0].from_date,
                                'to_date': data[0].to_date,
                             },
                })
            return result
        else:
            # We should log an error here
            return {'type': 'ir.actions.act_window_close'}

date_wizard()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:


