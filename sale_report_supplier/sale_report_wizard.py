# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2013 credativ Ltd (<http://credativ.co.uk>).
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


from osv import osv, fields
from tools.translate import _
from datetime import datetime, timedelta

class wizard_supplier_report(osv.osv_memory):
    _name = "sale.order.wizard_supplier_report"
    _description = "Sales by Supplier"
    _columns = {
            'date_from' : fields.date('From'),
            'date_to' : fields.date('To'),
        }

    def run_report(self, cr, uid, ids, context=None):
        if not context:
            context = {}

        rec_ids = context.get('active_ids', False)
        assert rec_ids, _('Active IDs is not set in Context')

        data = self.browse(cr, uid, ids, context=context)
        if data and data[0]:
            context.update({'date_from': data[0].date_from, 'date_to': data[0].date_to})

        return {
                'type': 'ir.actions.report.xml',
                'report_name': 'sale.supplier',
                'datas': {
                            'ids': rec_ids,
                            'model': 'res.partner',
                            'form': {}
                        },
                'context': context,
            }

wizard_supplier_report()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
