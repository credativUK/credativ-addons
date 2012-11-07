# -*- coding: utf-8 -*-
##############################################################################
#    
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
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

import time

from osv import osv, fields
from tools.translate import _

class overdue_report(osv.osv_memory):
    _name = 'overdue.report'
    _description = 'Overdue Payments'

    _columns = {
        'date_from': fields.date('Start date'),
        'date_to': fields.date('End date'),
        'partner_selection': fields.selection([('all', 'All Partners'),('selected', 'Selected Partners')], 'Display Accounts'),
        'partner_ids' : fields.many2many('res.partner', 'res_partner_overdue_rel', 'partner_id', 'overdue_id', 'Partners'),
        }

    def print_report(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        data={}
        data['ids'] = context['active_ids']
        data['form'] = self.read(cr, uid, ids, ['date_from', 'date_to', 'partner_ids', 'partner_selection'])[0]
        data['form']['context'] = context
        if context.get('active_model', False) == 'res.partner':
            data['form'].update({'partner_ids':context['active_ids']})
        
        if data['form']['partner_selection'] == 'all':
            data['form'].update({'partner_ids': self.pool.get('res.partner').search(cr, uid, [], context=context)})
            
        if data['form']['date_from'] > data['form']['date_to']:
            raise osv.except_osv(_('Warning'),_('Start Date should be smaller than End Date'))

        if not data['form']['partner_ids']:
            raise osv.except_osv(_('Warning'),_('Select a partner!'))
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'overdue.payment',
            'datas': data,
            }

overdue_report()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: