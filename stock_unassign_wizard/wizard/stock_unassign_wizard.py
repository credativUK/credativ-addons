# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution   
#    Copyright (C) 2013 credativ ltd (<http://www.credativ.co.uk>). All Rights Reserved
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from osv import osv, fields
from tools.translate import _
import decimal_precision as dp

class stock_unassign_wizard(osv.osv_memory):
    _name = 'stock.unassign.wizard'
    _description = 'Stock Unassign Wizard'
    _rec_name = 'picking_id'

    def _get_confirmed_moves(self, cr, uid, ids, name, arg, context=None):
        move_obj = self.pool.get('stock.move')
        res = {}
        for obj in self.read(cr, uid, ids, ['picking_id'], context=context):
            move_ids = move_obj.search(cr, uid, [('picking_id', '=', obj['picking_id'][0]), ('state', '=', 'confirmed')], context=context)
            res[obj['id']] = move_ids
        return res

    _columns = {
        'picking_id': fields.many2one('stock.picking', 'Picking', required=True, readonly=True,),
        'move_ids': fields.function(_get_confirmed_moves, type='one2many', relation='stock.move', string='Move Lines', readonly=True,),
        'other_move_ids': fields.one2many('stock.unassign.wizard.line', 'stock_unassign_id', 'Other Moves', readonly=True,),
        'error_on_fail': fields.boolean('Error on Failure', help="If selected, show an error and abort all changes if not all of the 'Moves to Assign' are assigned. \n" \
            "If not selected and not all of the 'Moves to Assign' are assigned, the selected 'Moves to Unassign' will be left unassigned.")
    }

    _defaults = {
        'error_on_fail': True,
    }

    def create(self, cr, uid, vals={}, context=None):
        if vals.get('picking_id'):
            move_ids = []
            pick_obj = self.pool.get('stock.picking')
            stock_obj = self.pool.get('stock.move')
            pick = pick_obj.browse(cr, uid, vals.get('picking_id'), context=context)
            for move in pick.move_lines:
                if move.state != 'confirmed':
                    continue
                m_ids = stock_obj.search(cr, uid, [ ('product_id', '=', move.product_id.id),
                                                    ('location_id', '=', move.location_id.id),
                                                    ('state', '=', 'assigned'),
                                                    ('picking_id', '!=', vals.get('picking_id'))], context=context)
                move_ids.extend(m_ids)
            if move_ids:
                other_move_ids = [[0, 0, {'move_id': x}] for x in move_ids]
                vals.update({'other_move_ids': other_move_ids})
        res = super(stock_unassign_wizard, self).create(cr, uid, vals, context=context)
        return res

    def action_assign(self, cr, uid, ids, context=None):
        if context == None:
            context = {}
        ctx = context.copy()
        ctx.update({'skip_stock_unassign_wizard': True})
        move_obj = self.pool.get('stock.move')
        pick_obj = self.pool.get('stock.picking')

        for rec in self.browse(cr, uid, ids, context=ctx):
            unassign_ids = []
            for move in rec.other_move_ids:
                if move.move_id.state != 'assigned':
                    raise osv.except_osv(_('Error!'),_("The state of one or more of the 'Moves to Unassign' has changed since this wizard was launched. Please close and relaunch this wizard."))
                if move.state == 'unassign':
                    unassign_ids.append(move.move_id.id)
            move_obj.cancel_assign(cr, uid, unassign_ids, context=ctx)
            res = pick_obj.action_assign(cr, uid, [rec.picking_id.id,], context=ctx)
            if res != True and rec.error_on_fail:
                raise osv.except_osv(_('Error!'),_("After unassigning the selected 'Moves to Unassign' there is still not enough stock to assign the 'Moves to Assign'. Please unassign additional stock moves, or if not possible there may not be enough stock present in this location."))
        return {'type': 'ir.actions.act_window_close'}

stock_unassign_wizard()

class stock_unassign_wizard_line(osv.osv_memory):
    _name = 'stock.unassign.wizard.line'
    _description = 'Stock Unassign Wizard Line'
    _rec_name = 'move_id'

    _columns = {
        'stock_unassign_id': fields.many2one('stock.unassign.wizard', 'Unassign Wizard', required=True, readonly=True),
        'state': fields.selection([('assign', 'Leave Assigned'), ('unassign', 'Unassign')], 'Action', size=10, required=True),
        'move_id': fields.many2one('stock.move', 'Name', required=True, readonly=True),
        'picking_id': fields.related('move_id', 'picking_id', type='many2one', relation='stock.picking', string='Reference', readonly=True, store=True),
        'origin': fields.related('move_id', 'picking_id', 'origin', type='char', size=64, string='Origin', readonly=True, store=True),
        'partner_id': fields.related('move_id', 'picking_id', 'address_id', 'partner_id', type='many2one', relation='res.partner', string='Partner', readonly=True, store=True),
        'product_id': fields.related('move_id', 'product_id', type='many2one', relation='product.product', string='Product', readonly=True, store=True),
        'product_qty': fields.related('move_id', 'product_qty', type='float', string='Quantity', digits_compute=dp.get_precision('Product UoM'), readonly=True, store=True),
        'product_uom': fields.related('move_id', 'product_uom', type='many2one', relation='product.uom', string='UoM', readonly=True, store=True),
        'product_uos': fields.related('move_id', 'product_uos', type='many2one', relation='product.uom', string='UoS', readonly=True, store=True),
        'prodlot_id': fields.related('move_id', 'prodlot_id', type='many2one', relation='stock.production.lot', string='Production Lot', readonly=True, store=True),
        'location_id': fields.related('move_id', 'location_id', type='many2one', relation='stock.location', string='Source Location', readonly=True, store=True),
        'location_dest_id': fields.related('move_id', 'location_dest_id', type='many2one', relation='stock.location', string='Destination Location', readonly=True, store=True),
        'date': fields.related('move_id', 'date', type='date', string='Date', readonly=True, store=True),
        'date_expected': fields.related('move_id', 'date_expected', type='date', string='Scheduled Date', readonly=True, store=True),
    }

    _defaults = {
        'state': 'assign',
    }

    def action_assign(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'assign',}, context=context)
        return True

    def action_unassign(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'unassign',}, context=context)
        return True

stock_unassign_wizard_line()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
