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

class account_move_line(osv.osv):
    _inherit = "account.move.line"

    def _query_get(self, cr, uid, obj='l', context=None):
        query = super(account_move_line, self)._query_get(cr, uid, obj=obj, context=context)
        if context.get('partner_filter', False) and not context.get('partner_filter_loop', False):
            ctx = context.copy()
            ctx['partner_filter_loop'] = True
            partner_query = self.pool.get('res.partner')._where_calc(cr, uid, eval(context['partner_filter']), context=ctx)
            if partner_query:
                from_clause, where_clause, where_clause_params = partner_query.get_sql()
                where_str = where_clause and (" WHERE %s" % where_clause) or ''
                subquery = 'SELECT res_partner."id" FROM %s %s' % (from_clause, where_str % tuple(map(repr, where_clause_params)))
                query += " AND "+obj+".partner_id IN (%s)" % subquery.replace('%', '%%')
        return query

class account_aged_trial_balance(osv.osv_memory):
    _inherit = 'account.aged.trial.balance'

    _columns = {
        'partner_filter_id': fields.many2one('ir.filters', 'Partner Filter', domain=[('model_id', '=', 'res.partner')], help='Select a filter for partners. New filter can be created from the customers screen.'),
    }

    def _build_contexts(self, cr, uid, ids, data, context=None):
        res = super(account_aged_trial_balance, self)._build_contexts(cr, uid, ids, data, context=context)
        partner_filter_id = self.read(cr, uid, ids, ['partner_filter_id'], context=context)[0]['partner_filter_id']
        if partner_filter_id:
            partner_filter_domain = self.pool.get('ir.filters').read(cr, uid, [partner_filter_id[0]], ['domain'], context=context)[0]['domain']
            if partner_filter_domain:
                res['partner_filter'] = partner_filter_domain
        return res

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
