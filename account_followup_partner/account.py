# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution   
#    Copyright (C) 2014 credativ ltd (<http://www.credativ.co.uk>). All Rights Reserved
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
from tools.safe_eval import safe_eval as eval

class account_followup_print(osv.osv_memory):
    _inherit = 'account.followup.print'

    _columns = {
        'partner_filter_id': fields.many2one('ir.filters', 'Partner Filter', domain=[('model_id', '=', 'res.partner')], help='Select a filter for partners. New filter can be created from the customers screen.'),
    }

    def do_continue(self, cr, uid, ids, context=None):
        res = super(account_followup_print, self).do_continue(cr, uid, ids, context=context)
        data = self.browse(cr, uid, ids, context=context)[0]
        res['context'].update({'partner_filter_id': data.partner_filter_id.id})
        return res

class account_followup_print_all(osv.osv_memory):
    _inherit = 'account.followup.print.all'

    def _get_partners_followp(self, cr, uid, ids, context=None):
        res = super(account_followup_print_all, self)._get_partners_followp(cr, uid, ids, context=context)
        if context is None:
            context = {}
        if context.get('partner_filter_id'):
            stat_obj = self.pool.get('account_followup.stat.by.partner')
            partner_filter = self.pool.get('ir.filters').read(cr, uid, [context['partner_filter_id']], ['domain'], context=context)[0]['domain']

            ctx = context.copy()
            ctx['partner_filter_loop'] = True
            partner_query = self.pool.get('res.partner')._where_calc(cr, uid, eval(partner_filter), context=ctx)
            if partner_query:
                from_clause, where_clause, where_clause_params = partner_query.get_sql()
                where_str = where_clause and (" WHERE %s" % where_clause) or ''
                subquery = 'SELECT res_partner."id" FROM %s %s' % (from_clause, where_str % tuple(map(repr, where_clause_params)))

                if res['partner_ids']:
                    query = 'SELECT id FROM account_followup_stat_by_partner WHERE id IN (%s) AND partner_id IN (%s);' % (','.join([str(i) for i in res['partner_ids']]), subquery)
                    cr.execute(query)
                    res['partner_ids'] = [i[0] for i in cr.fetchall()]

                if res['to_update']:
                    query = 'SELECT id FROM account_followup_stat_by_partner WHERE id IN (%s) AND partner_id IN (%s);' % (','.join([str(i[1]['partner_id']) for i in res['to_update'].iteritems()]), subquery)
                    cr.execute(query)
                    update_ids = [u[0] for u in cr.fetchall()]
                    res['to_update'] = dict([i for i in res['to_update'].iteritems() if i[1]['partner_id'] in update_ids])

        return res

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
