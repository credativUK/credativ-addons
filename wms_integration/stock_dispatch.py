# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution   
#    Copyright (C) 2012 credativ ltd (<http://www.credativ.co.uk>). All Rights Reserved
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
import netsvc
import logging
from datetime import datetime
import pooler
import os
DEBUG = True

_logger = logging.getLogger(__name__)

class stock_dispatch(osv.osv):
    _inherit = "stock.dispatch"
    
    def wms_export_all(self, cr, uid, ids, context=None):
        if context == None:
            context = {}
        move_pool = self.pool.get('stock.move')
        data_pool = self.pool.get('ir.model.data')
        
        final_move_ids = []
        wms_sm_sequence = {}
        
        for dispatch in self.browse(cr, uid, ids, context=context):
            address_groups = {}
            for move in dispatch.stock_moves: # Group moves by the customer delivery address
                address_groups.setdefault(move.address_id.id, []).append(move)

            for address_id, moves in address_groups.iteritems():
                move_ids = []
                for move in moves:
                    rec_check_ids = data_pool.search(cr, uid, [('model', '=', 'stock.move'), ('res_id', '=', move.id), ('module', 'ilike', 'extref'), ('external_referential_id', '=', dispatch.warehouse_id.referential_id.id)])
                    
                    if rec_check_ids:
                        rec_checks = data_pool.browse(cr, uid, rec_check_ids, context=context)
                        rec_check_ids = []
                        for rec_check in rec_checks:
                            try:
                                dispatch_name, address_name, sm_seq = rec_check.name.split('/')[1].split('_')
                                sm_seq = int(sm_seq)
                                if dispatch_name == dispatch.name and address_name == '%d' % (address_id,):
                                    rec_check_ids.append(rec_check.id)
                            except Exception, e:
                                # Something is wrong with this referential, delete it and create a new one
                                data_pool.unlink(cr, uid, rec_check.id, context=context)
                                rec_check_ids = []
                            else:
                                wms_sm_sequence[move.id] = sm_seq
                                if move.state == 'cancel' or move.dispatch_id.id != dispatch.id:
                                    continue
                                move_ids.append(move.id)
                                ir_model_data_rec = {
                                    'name': rec_check.name,
                                    'model': rec_check.model,
                                    'external_log_id': context.get('external_log_id', None),
                                    'res_id': rec_check.res_id,
                                    'external_referential_id': rec_check.external_referential_id.id,
                                    'module': 'pendref/' + rec_check.external_referential_id.name}
                                data_pool.create(cr, uid, ir_model_data_rec)
                    else:
                        if move.state == 'cancel':
                            continue
                        cr.execute("""SELECT
                                    MAX(COALESCE(SUBSTRING(name from 'stock_move/%s_%d_([0-9]*)'), '0')::INTEGER) + 1
                                    FROM ir_model_data imd
                                    WHERE external_referential_id = %s
                                    AND model = 'stock.move'
                                    AND (module ilike 'extref%%'
                                    OR module ilike 'pendref%%')""" % (dispatch.name, address_id, dispatch.warehouse_id.referential_id.id,))
                        number = cr.fetchall()
                        if number and number[0][0]:
                            sm_seq = number[0][0]
                        else:
                            sm_seq = 1
                        
                        ir_model_data_rec = {
                            'name': "stock_move/%s_%d_%d" % (dispatch.name, address_id, sm_seq),
                            'model': 'stock.move',
                            'external_log_id': context.get('external_log_id', None),
                            'res_id': move.id,
                            'external_referential_id': dispatch.warehouse_id.referential_id.id,
                            'module': 'pendref/' + dispatch.warehouse_id.referential_id.name}
                        data_pool.create(cr, uid, ir_model_data_rec)
                        
                        wms_sm_sequence[move.id] = sm_seq
                        move_ids.append(move.id)
                final_move_ids.extend(move_ids)
        
        if final_move_ids:
            ctx = context.copy()
            ctx.update({'wms_sm_sequence': wms_sm_sequence})
            if dispatch.warehouse_id.mapping_dispatch_orders_id:
                ctx.update({'external_mapping_ids': [dispatch.warehouse_id.mapping_dispatch_orders_id.id,]})

            self.pool.get('external.referential')._export(cr, uid, dispatch.warehouse_id.referential_id.id, 'stock.move', final_move_ids, context=ctx)
        else:
            raise # FIXME: Something went very wrong here

        return
    
    def wms_export_orders(self, cr, uid, ids, referential_id, context=None):
        if context == None:
            context = {}
        data_pool = self.pool.get('ir.model.data')

        export_dispatch_ids = []
        external_log_id = False
        
        for dispatch in self.browse(cr, uid, ids):
            if not dispatch.warehouse_id or not dispatch.warehouse_id.referential_id:
                continue
            
            try:
                ext_id = self.oeid_to_extid(cr, uid, dispatch.id, dispatch.warehouse_id.referential_id.id, context=context)
                if not ext_id: # We should only export new dispatches
                    if not external_log_id:
                        external_log_id = self.pool.get('external.log').start_transfer(cr, uid, [], referential_id, 'stock.dispatch', context=context) # FIXME: Move these around each dispatch object so we can export many
                        context['external_log_id'] = external_log_id
                    ir_model_data_rec = {
                        'name': 'stock_dispatch/' + dispatch.name,
                        'model': 'stock.dispatch',
                        'external_log_id': external_log_id,
                        'res_id': dispatch.id,
                        'external_referential_id': dispatch.warehouse_id.referential_id.id,
                        'module': 'pendref/' + dispatch.warehouse_id.referential_id.name}
                    data_pool.create(cr, uid, ir_model_data_rec, context=context)
                    export_dispatch_ids.append(dispatch.id)
                else: # Exported already, skip
                    continue
            
            except Exception, e:
                raise
                pass

        if export_dispatch_ids:
            self.wms_export_all(cr, uid, export_dispatch_ids, context=context)
            self.pool.get('external.log').end_transfer(cr, uid, external_log_id, context=context)
            
        return True

    def wms_import_moves(self, cr, uid, ids, move_lines, context=None):
        if not context:
            context = {}
        ctx = context.copy()
        sm_obj = self.pool.get('stock.move')
        wkf_service = netsvc.LocalService('workflow')
        
        stock_moves = sm_obj.browse(cr, uid, move_lines.keys(), context=ctx)
        dispatch_dict = {}
        
        for stock_move in stock_moves:
            if not stock_move.dispatch_id:
                _logger.warn('Stock move %d dispatched but not part of a dispatch.' % (stock_move.id, stock_move.state,))
                ctx['from_dispatch'] = False
                sm_obj.action_done(cr, uid, stock_move.id, context=ctx)
            else:
                dispatch_dict.setdefault(stock_move.dispatch_id, []).append(stock_move)
        
        for dispatch, moves in dispatch_dict.iteritems():
            dispatch_moves = set([x.id for x in dispatch.stock_moves])
            done_moves = set([x.id for x in moves])
            not_done_moves = list(dispatch_moves.difference(done_moves))
            
            ctx['from_dispatch'] = dispatch.id
            sm_obj.action_done(cr, uid, list(done_moves), context=ctx)
            
            if not_done_moves:
                _logger.error('Stock moves %s were part of dispatch %s but not completed, Unable to complete dispatch.' % (not_done_moves, dispatch.name,))
            else:
                wkf_service.trg_validate(uid, 'stock.dispatch', dispatch.id, 'done', cr)
                _logger.info('Dispatch %s complted.' % (dispatch.name,))
        
        return

stock_dispatch()
