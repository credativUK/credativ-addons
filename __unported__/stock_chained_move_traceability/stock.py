# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2014 credativ Ltd (<http://credativ.co.uk>).
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

from osv import osv, fields

class StockMove(osv.Model):
    _inherit = 'stock.move'


    def _find_related_moves(self, cr, uid, id, relation, context=None):
        moves = []
        inverse_relation = relation == 'child_id' and 'parent_id' or 'child_id'
        sql = '''WITH RECURSIVE move_relation(child_id, parent_id) AS (
                     SELECT child_id, parent_id from stock_move_history_ids where %s = %%s
                     UNION ALL
                     SELECT sm.child_id, sm.parent_id
                     FROM move_relation mr, stock_move_history_ids sm
                     WHERE sm.%s = mr.%s
                 )
                 SELECT %s FROM move_relation''' % (relation, relation, inverse_relation, inverse_relation)
        cr.execute(sql, (str(id),))
        res = cr.fetchall()
        return [i[0] for i in res]


    def _calc_chained_moves(self, cr, uid, ids, fields, arg, context=None):
        chained_moves = {}
        ids = isinstance(ids, list) and ids or [ids]
        for id in ids:
            chained_moves[id] = []
            for relation in ['child_id', 'parent_id']:
                chained_moves[id].extend(self._find_related_moves(cr, uid, id, relation, context=context))
        return chained_moves


    _columns = {
            'chained_moves' : fields.function(_calc_chained_moves, type='many2many', relation='stock.move', string='Chained Moves'),
    }



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
