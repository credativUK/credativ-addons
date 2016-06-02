# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2016 credativ ltd (<http://www.credativ.co.uk>). All Rights Reserved
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

from openerp.osv import osv

OK_STATES = set(['cancel', 'done', 'assigned'])


class StockPicking(osv.Model):
    _name = 'stock.picking'
    _inherit = 'stock.picking'


    def to_bundles(self, cr, uid, ids, context=None):
        """ Groups together bundled lines, returning
        """

        if hasattr(ids, '__iter__'):
            return {id : self.to_bundles(cr, uid, id, context=context) for id in ids}

        bundles = {}
        non_bundled_moves = []
        pick = self.browse(cr, uid, ids, context=context)
        for move in pick.move_lines:
            bundle = move.sale_parent_line_id.id
            if bundle:
                if bundles.get(bundle) is None:
                    bundles.update({bundle : []})
                bundles[bundle].append(move)
            else:
                non_bundled_moves.append(move)
        return bundles, non_bundled_moves


    def test_assigned(self, cr, uid, ids):
        # Call super in case any other hooks need to be triggered
        res = super(StockPicking, self).test_assigned(cr, uid, ids)

        if not res:
            return res

        ok = True
        for pick in self.browse(cr, uid, ids):
            mt = pick.move_type

            if pick.type == 'in' or not mt == 'direct':
                return res

            bundles, non_bundled_moves = self.to_bundles(cr, uid, pick.id)

            for bundle in bundles:
                # super() should have called check_assign() for 'waiting' moves
                move_states = [move.state for move in bundles[bundle]]
                move_states_with_qty = [move.state for move in bundles[bundle] if move.product_qty]
                if all(state == 'assigned' for state in move_states_with_qty):
                    return True
                if not set(move_states).issubset(OK_STATES):
                    ok = False

            for move in non_bundled_moves:
                if (move.state == 'assigned') and (move.product_qty):
                    return True
                if move.state not in OK_STATES:
                    ok = False

        return ok

