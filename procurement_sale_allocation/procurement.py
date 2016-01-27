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

from osv import osv, fields
from openerp.tools.translate import _
import netsvc

class ProcurementOrder(osv.Model):
    _inherit = 'procurement.order'

    def _verify_wkf_change(self, cr, uid, proc_id, acts, po_id, context=None):
        query = """SELECT wa.name, wi_sub.res_id
            FROM wkf_instance wi
            INNER JOIN wkf_workitem ww ON ww.inst_id = wi.id
            INNER JOIN wkf_activity wa ON wa.id = ww.act_id
            LEFT OUTER JOIN wkf_instance wi_sub ON wi_sub.id = ww.subflow_id
                AND wi_sub.res_type = 'purchase.order'
            WHERE wi.res_id = %s
            AND wi.res_type = 'procurement.order'"""
        cr.execute(query, (proc_id,))
        res = cr.fetchall()
        if not res:
            raise osv.except_osv(_('Error !'), _('Unable to find active workflow workitem for procurement id %s') % (proc_id,))
        if len(res) > 1:
            raise osv.except_osv(_('Error !'), _('Found multiple active workflow workitems for procurement id %s') % (proc_id,))
        if res[0][0] not in acts:
            raise osv.except_osv(_('Error !'), _('Unexpected procurement workflow activity %s, expected %s for procurement id %s') % (res[0][0], acts, proc_id,))
        if res[0][1] and res[0][1] != po_id:
            raise osv.except_osv(_('Error !'), _('Procurement id %s workflow linked to subflow for purchase id %s, should be %s') % (proc_id, res[0][1] or 'None', po_id or 'None'))
        return True

    def write(self, cr, uid, ids, values, context=None):
        if context is None:
            context = {}
        purchase_obj = self.pool.get('purchase.order')
        purchase_line_obj = self.pool.get('purchase.order.line')
        wkf_service = netsvc.LocalService('workflow')

        procs = []
        if ids and 'purchase_id' in values:
            procs = self.read(cr, uid, ids, ['purchase_id', 'name', 'procure_method', 'move_id', 'product_id', 'state'], context=context) # This must be a read since we need the 'before' data
        res = super(ProcurementOrder, self).write(cr, uid, ids, values, context=context)

        signals = {}
        purchase_orig_ids, purchase_new_ids = set(), set()
        for proc in procs:
            if proc['state'] in ['draft', 'confirmed', 'exception']:
                continue
            if (proc['purchase_id'] and proc['purchase_id'][0] or False) != values['purchase_id']:
                signal = None
                purchase_orig = proc['purchase_id'] or False
                purchase_new = values['purchase_id'] or False
                pol_ids = []
                if proc['move_id']:
                    pol_ids = purchase_line_obj.search(cr, uid, [('move_dest_id', '=', proc['move_id'][0]), ('state', '!=', 'cancel'), ('order_id.state', '!=', 'cancel'), ('product_id', '=', proc['product_id'][0])], context=context)
                if not purchase_orig and pol_ids: # This is an MTO order being created, take no action
                    signal = None
                elif purchase_orig and not purchase_new and proc['procure_method']=='make_to_order' and context.get('psa_proc_removed'):
                    signal = 'signal_mto_mto_confirm'
                elif not purchase_orig and purchase_new:
                    signal = 'signal_mts_mto'
                elif (purchase_orig and not purchase_new) or (proc['procure_method']=='make_to_order' and not purchase_new):
                    signal = 'signal_mto_mts'
                elif purchase_orig and purchase_new or (proc['procure_method']=='make_to_order' and purchase_new):
                    signal = 'signal_mto_mto'
                if signal:
                    signals.setdefault(signal, []).append((proc['id'], purchase_orig[0], purchase_new))
                    if purchase_orig:
                        purchase_orig_ids.add(purchase_orig[0])
                    if purchase_new:
                        purchase_new_ids.add(purchase_new)

        context.update({'psa_skip_moves': True})

        # Check PO restrictions
        purchase_ids = []
        purchase_ids = purchase_obj.search(cr, uid, ['|', ('id', 'in', list(purchase_new_ids)), '&', ('id', 'in', list(purchase_orig_ids)), ('state', '!=', 'cancel')], context=context)
        if not context.get('force_po_unassign') and (purchase_orig_ids or purchase_new_ids):
            purchase_restrict_ids = purchase_obj.allocate_check_restrict(cr, uid, purchase_ids, context=context)
            purchase_restrict_names = [x['name'] for x in purchase_obj.read(cr, uid, purchase_restrict_ids, ['name',], context=context)]
            raise osv.except_osv(_('Error!'),_('The following purchase orders do not allow stock to be allocated or deallocated: %s') % (purchase_restrict_names,))

        # Read PO names
        purchase_name_dict = {}
        if purchase_ids:
            purchase_names = purchase_obj.read(cr, uid, purchase_ids, ['name'], context=context)
            for purchase_name in purchase_names:
                purchase_name_dict[purchase_name['id']] = purchase_name['name']

        # TODO: Refactor this part for less code
        if signals.get('signal_mto_mto_confirm'):
            signal = 'signal_mto_mto_confirm'
            expected_acts = (('confirm_mto', 'buy', 'ready',), ('confirm',))
            proc_ids = [x[0] for x in signals.get('signal_mto_mto_confirm')]
            self.write(cr, uid, proc_ids, {'state': 'confirmed', 'procure_method': 'make_to_order', 'message': False}, context=context)
            self._cancel_stock_assign(cr, uid, proc_ids, context=context)
            for proc_data in signals.get('signal_mto_mto_confirm'):
                self._verify_wkf_change(cr, uid, proc_data[0], expected_acts[0], proc_data[1], context=context)
                wkf_service.trg_validate(uid, 'procurement.order', proc_data[0], signal, cr)
                self._verify_wkf_change(cr, uid, proc_data[0], expected_acts[1], proc_data[2] or False, context=context)
                message = _("Procurement deallocated from PO (%s) to MTO") % (purchase_name_dict[proc_data[1]],)
                self.message_post(cr, uid, [proc_data[0]], body=message, context=context)

        if signals.get('signal_mts_mto'):
            signal = 'signal_mts_mto'
            expected_acts = (('confirm_mts', 'make_to_stock', 'ready',), ('buy',))
            proc_ids = [x[0] for x in signals.get('signal_mts_mto')]
            self.write(cr, uid, proc_ids, {'state': 'running', 'procure_method': 'make_to_order', 'message': False}, context=context)
            self._cancel_stock_assign(cr, uid, proc_ids, context=context)
            for proc_data in signals.get('signal_mts_mto'):
                self._verify_wkf_change(cr, uid, proc_data[0], expected_acts[0], proc_data[1], context=context)
                wkf_service.trg_validate(uid, 'procurement.order', proc_data[0], signal, cr)
                self._verify_wkf_change(cr, uid, proc_data[0], expected_acts[1], proc_data[2] or False, context=context)
                message = _("Procurement allocated from MTS to PO (%s)") % (purchase_name_dict[proc_data[2]],)
                self.message_post(cr, uid, [proc_data[0]], body=message, context=context)

        if signals.get('signal_mto_mts'):
            signal = 'signal_mto_mts'
            expected_acts = (('confirm_mto', 'buy', 'ready',), ('confirm_mts', 'cancel', 'ready', 'done'))
            proc_ids = [x[0] for x in signals.get('signal_mto_mts')]
            self.write(cr, uid, proc_ids, {'state': 'exception', 'procure_method': 'make_to_stock', 'message': False}, context=context)
            self._cancel_stock_assign(cr, uid, proc_ids, context=context)
            self._cancel_po_assign(cr, uid, proc_ids, context=context)
            for proc_data in signals.get('signal_mto_mts'):
                # It is not possible to break out of a subflow unless we get a signal from it, we force it to be complete here
                cr.execute('select id, wkf_id from wkf_instance where res_id=%s and res_type=%s', (proc_data[0], 'procurement.order'))
                for inst_id, wkf_id in cr.fetchall():
                    cr.execute('update wkf_workitem set state=%s where inst_id=%s', ('complete', inst_id))

                self._verify_wkf_change(cr, uid, proc_data[0], expected_acts[0], proc_data[1], context=context)
                wkf_service.trg_validate(uid, 'procurement.order', proc_data[0], signal, cr)
                self._verify_wkf_change(cr, uid, proc_data[0], expected_acts[1], proc_data[2] or False, context=context)
                message = _("Procurement deallocated from PO (%s) to MTS") % (purchase_name_dict[proc_data[1]],)
                self.message_post(cr, uid, [proc_data[0]], body=message, context=context)

        if signals.get('signal_mto_mto'):
            signal = 'signal_mto_mto'
            expected_acts = (('confirm_mto', 'buy', 'ready',), ('buy',))
            proc_ids = [x[0] for x in signals.get('signal_mto_mto')]
            self.write(cr, uid, proc_ids, {'state': 'running', 'procure_method': 'make_to_order', 'message': False}, context=context)
            self._cancel_stock_assign(cr, uid, proc_ids, context=context)
            self._cancel_po_assign(cr, uid, proc_ids, context=context)
            for proc_data in signals.get('signal_mto_mto'):
                # It is not possible to break out of a subflow unless we get a signal from it, we force it to be complete here
                cr.execute('select id, wkf_id from wkf_instance where res_id=%s and res_type=%s', (proc_data[0], 'procurement.order'))
                for inst_id, wkf_id in cr.fetchall():
                    cr.execute('update wkf_workitem set state=%s where inst_id=%s', ('complete', inst_id))

                self._verify_wkf_change(cr, uid, proc_data[0], expected_acts[0], proc_data[1], context=context)
                wkf_service.trg_validate(uid, 'procurement.order', proc_data[0], signal, cr)
                self._verify_wkf_change(cr, uid, proc_data[0], expected_acts[1], proc_data[2] or False, context=context)
                message = _("Procurement reallocated from PO (%s) to PO (%s)") % (purchase_name_dict[proc_data[1]], purchase_name_dict[proc_data[2]])
                self.message_post(cr, uid, [proc_data[0]], body=message, context=context)

        return res

    def _confirm_po_assign(self, cr, uid, ids, context=None): # TODO: Improvements????
        move_obj = self.pool.get('stock.move')
        purchase_line_obj = self.pool.get('purchase.order.line')
        purchase_obj = self.pool.get('purchase.order')
        uom_obj = self.pool.get('product.uom')
        for proc in self.browse(cr, uid, ids, context=context):
            # Find all PO lines with no move_dest_id
            pol_ids = purchase_line_obj.search(cr, uid, [('move_dest_id', '=', False), ('state', '!=', 'cancel'), ('order_id', '=', proc.purchase_id.id), ('product_id', '=', proc.product_id.id)], order="date_planned desc, product_qty asc", context=context)
            pol_assign_id = False
            for line in purchase_line_obj.browse(cr, uid, pol_ids, context=context):
                if any([move.state in ('done', 'cancel') for move in line.move_ids]):
                    # Only allow allocation to lines with no moves (draft) or available moves (in progress)
                    continue
                purchase_uom_qty = uom_obj._compute_qty(cr, uid, proc.product_uom.id, proc.product_qty, line.product_uom.id)
                if line.product_qty >= purchase_uom_qty:
                    pol_assign_id = line.id
                    break
            if not pol_assign_id:
                raise osv.except_osv(_('Error!'),_("The purchase order %s does not have enough space to allocate procurement %s.") % (proc.purchase_id.name, proc.name))
            # If qty < pol.qty, duplicate POL and move and divide the qty
            pol_assign_id, pol_new_id = purchase_line_obj.do_split(cr, uid, pol_assign_id, purchase_uom_qty, context=context)
            # Set the move_dest_id from the PO line and it's move
            pol_assign = purchase_line_obj.browse(cr, uid, pol_assign_id, context=context)
            purchase_line_obj.write(cr, uid, [pol_assign.id,], {'move_dest_id': proc.move_id.id}, context=context)
            move_obj.write(cr, uid, [x.id for x in pol_assign.move_ids], {'move_dest_id': proc.move_id.id}, context=context)
        self.write(cr, uid, ids, {'state': 'running'}, context=context)
        return True

    def _cancel_po_assign(self, cr, uid, ids, context=None):
        if context == None:
            context = {}
        ctx = context.copy()
        ctx.update({'from_picking': True}) # This is required to support the WMS integration - the move is not actually being cancelled, just re-arranged
        move_obj = self.pool.get('stock.move')
        purchase_obj = self.pool.get('purchase.order')
        purchase_line_obj = self.pool.get('purchase.order.line')

        to_unassign = []
        move_obj = self.pool.get('stock.move')
        for proc_data in self.read(cr, uid, ids, ['move_id']):
            if proc_data['move_id']:
                to_unassign.append(proc_data['move_id'][0])

        pol_ids = purchase_line_obj.search(cr, uid, [('move_dest_id', 'in', to_unassign), ('order_id.state', '!=', 'cancel')], context=ctx)
        skip_condition = ('skip_pol_remove' in purchase_obj._columns) and [('order_id.skip_pol_remove', '=', True)] or []
        draft_pol_ids = purchase_line_obj.search(cr, uid, [('move_dest_id', 'in', to_unassign), ('order_id.state', '=', 'draft')] + skip_condition, context=ctx)

        if pol_ids:
            # Remove the move_dest_id from this PO line and the PO lines moves
            draft_purchase_line_data = purchase_line_obj.read(cr, uid, draft_pol_ids, ['order_id'], context=ctx)
            purchase_line_data = purchase_line_obj.read(cr, uid, pol_ids, ['order_id'], context=ctx)
            purchase_line_obj.write(cr, uid, pol_ids, {'move_dest_id': False}, context=ctx)
            # If the PO is still in draft and we cancel the procurement we can safely discard the PO line completly
            purchase_line_obj.unlink(cr, uid, draft_pol_ids, context=ctx)
            # Adjust the PO moves - Find all linked to a PO line since a partial picking could split a move with the same move_dest_id into 2 parts
            move_ids = move_obj.search(cr, uid, [('move_dest_id', 'in', to_unassign), ('purchase_line_id', '!=', False), ('state', '!=', 'cancel')], context=ctx)
            move_obj.write(cr, uid, move_ids, {'move_dest_id': False}, context=ctx)

            # Delete any POs which have no order lines and are draft
            draft_po_ids = list(set([x['order_id'][0] for x in draft_purchase_line_data]))
            for draft_po in purchase_obj.read(cr, uid, draft_po_ids, ['order_line'], context=ctx):
                if not len(draft_po['order_line']):
                    purchase_obj.unlink(cr, uid, [draft_po['id']], context=ctx)

            # Attempt to merge all lines for POs
            po_ids = list(set([x['order_id'][0] for x in purchase_line_data]))
            po_ids = purchase_obj.search(cr, uid, [('id', 'in', po_ids)], context=ctx) # Re-search as some may have just been deleted
            for po in purchase_obj.browse(cr, uid, po_ids, context=ctx):
                merge_pol_ids = [pol.id for pol in po.order_line if not pol.move_ids or all([sm.state == 'assigned' for sm in pol.move_ids])]
                if len(merge_pol_ids) > 1:
                    purchase_line_obj.do_merge(cr, uid, pol_ids, context=ctx)

        return True

    def _cancel_stock_assign(self, cr, uid, ids, context=None):
        to_unassign = []
        move_obj = self.pool.get('stock.move')
        for proc_data in self.read(cr, uid, ids, ['move_id']):
            if proc_data['move_id']:
                to_unassign.append(proc_data['move_id'][0])
        to_unassign = move_obj.search(cr, uid, [('id', 'in', to_unassign), ('state', '=', 'assigned')])
        if to_unassign:
            move_obj.cancel_assign(cr, uid, to_unassign, context=context)
        return True

    def action_cancel(self, cr, uid, ids):
        self._cancel_po_assign(cr, uid, ids)
        return super(ProcurementOrder, self).action_cancel(cr, uid, ids)

    def action_po_assign(self, cr, uid, ids, context=None): # TODO: Improvements (break out of workflow?)
        purchase_line_obj = self.pool.get('purchase.order.line')
        other_ids = []
        res = []
        if ids:
            for proc in self.browse(cr, uid, ids, context=context):
                pol_ids = purchase_line_obj.search(cr, uid, [('move_dest_id', '=', proc.move_id.id), ('state', '!=', 'cancel'), ('order_id', '=', proc.purchase_id.id), ('product_id', '=', proc.product_id.id)], context=context)
                if not pol_ids and proc.purchase_id:
                    res.append(proc.purchase_id.id)
                    self._confirm_po_assign(cr, uid, [proc.id,], context=context)
                else:
                    # If pol_ids has a value it is likely to be a new MTO order creating an RFQ
                    other_ids.append(proc.id)
        if other_ids:
            purchase_ids = super(ProcurementOrder, self).action_po_assign(cr, uid, other_ids, context=context)
            if purchase_ids:
                res.append(purchase_ids)
        return len(res) and res[0] or 0

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
