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

from openerp.osv import osv
from openerp import pooler

import logging
_logger = logging.getLogger(__name__)

class ProcurementOrder(osv.Model):
    _inherit = 'procurement.order'

    def _procure_confirm_mto_confirmed_to_mts_group(self, cr, uid, ids, use_new_cursor=False, context=None):
        if not ids:
            return

        bundle_ids = set()
        cr_orig = cr

        try:
            if use_new_cursor:
                cr = pooler.get_db(use_new_cursor).cursor()

            # Group procurements by individual bundle
            cr.execute("""SELECT
                            sol.line_parent_id,
                            ARRAY_AGG(proc.id)
                        FROM procurement_order proc
                        INNER JOIN stock_move sm
                            ON sm.id = proc.move_id
                        INNER JOIN sale_order_line sol
                            ON sol.id = sm.sale_line_id
                        WHERE proc.id IN %s
                        GROUP BY sol.line_parent_id
                        ORDER BY MIN(proc.date_planned)""", (tuple(ids),))
            bundle_procs = cr.fetchall()

            for parent_sol_id, procurement_ids in bundle_procs:
                bundle_ids.update(procurement_ids)

                cr.execute('SAVEPOINT mto_to_mts_group')

                # Run MTS function
                res = self._procure_confirm_mto_confirmed_to_mts_proc(cr, uid, procurement_ids, context=context)

                # Search for related procurements not included which are in an incompatible state
                # Any results from here means we cannot allocate the bundle procurements to stock
                cr.execute("""SELECT
                                proc.id
                            FROM procurement_order proc
                            INNER JOIN stock_move sm
                                ON sm.id = proc.move_id
                            INNER JOIN sale_order_line sol
                                ON sol.id = sm.sale_line_id
                            WHERE sol.line_parent_id = %s
                            AND proc.id NOT IN %s
                            AND proc.state NOT IN ('draft', 'cancel', 'done', 'ready')
                            AND NOT (proc.procure_method = 'make_to_stock'
                                    AND proc.state = 'running')""", (parent_sol_id, tuple(procurement_ids)))

                bad_proc_ids = [x[0] for x in cr.fetchall()]

                if res['fail'] or bad_proc_ids: # If any fail OR any others are not running MTS, draft, cancel, done or ready then fail
                    cr.execute('ROLLBACK TO SAVEPOINT mto_to_mts_group')
                    cr.execute("""UPDATE procurement_order set note = TRIM(both E'\n' FROM COALESCE(note, '') || %s) WHERE id in %s""", ('\n\n_mto_to_mts_done_', tuple(procurement_ids),))
                elif res['temp']: # May just be a temporary issue, rollback anyway then skip
                    cr.execute('ROLLBACK TO SAVEPOINT mto_to_mts_group')
                    cr.execute("""UPDATE procurement_order set note = TRIM(both E'\n' FROM COALESCE(note, '') || %s) WHERE id in %s""", ('\n\n_mto_to_mts_fail_', tuple(procurement_ids),))
                else: # Everything was OK, all bundle was changed to MTS
                    pass

                cr.execute('RELEASE SAVEPOINT mto_to_mts_group')

        finally:
            if use_new_cursor:
                cr.commit()
                cr.close()
                cr = cr_orig

        # For all other ids which are not part of a bundle, call super
        non_bundle_ids = list(set(ids).difference(bundle_ids))
        return super(self, ProcurementOrder)._procure_confirm_mto_confirmed_to_mts_group(cr, uid, non_bundle_ids, use_new_cursor=use_new_cursor, context=context)


