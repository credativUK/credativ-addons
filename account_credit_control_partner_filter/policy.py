# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 credativ ltd (<http://www.credativ.co.uk>). All Rights Reserved
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

from openerp.osv.orm import Model


class CreditControlPolicy(Model):

    _inherit = "credit.control.policy"

    def _move_lines_domain(self, cr, uid, policy, controlling_date,
                           context=None):

        if context is None:
            context = {}
        domains = super(CreditControlPolicy, self)._move_lines_domain(cr, uid,
                                                                  policy,
                                                                  controlling_date,
                                                                  context)

        if context.get('partner_filter_id'):
            partner_filter = self.pool.get('ir.filters').read(cr, uid,
                                                              [context['partner_filter_id']],
                                                              ['domain'],
                                                              context=context)[0]['domain']

            ctx = context.copy()
            ctx['partner_filter_loop'] = True
            partner_query = self.pool.get('res.partner')._where_calc(cr,
                                                                     uid,
                                                                     eval(partner_filter),
                                                                     context=ctx)
            if partner_query:
                from_clause, where_clause, where_clause_params = partner_query.get_sql()
                where_str = where_clause and (" WHERE %s" % where_clause) or ''
                subquery = 'SELECT res_partner."id" FROM %s %s' % (from_clause,
                                                                   where_str % tuple(map(repr, where_clause_params)))
                cr.execute(subquery)
                partner_ids = [i[0] for i in cr.fetchall()]
                domains.append(('partner_id', 'in', partner_ids))

        return domains

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

