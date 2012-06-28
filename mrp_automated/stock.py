## -*- encoding: utf-8 -*-
###############################################################################
##
##    OpenERP, Open Source Management Solution
##    Copyright (C) 2011 credativ ltd (<http://www.credativ.co.uk>). All Rights Reserved
##
##    This program is free software: you can redistribute it and/or modify
##    it under the terms of the GNU General Public License as published by
##    the Free Software Foundation, either version 3 of the License, or
##    (at your option) any later version.
##
##    This program is distributed in the hope that it will be useful,
##    but WITHOUT ANY WARRANTY; without even the implied warranty of
##    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
##    GNU General Public License for more details.
##
##    You should have received a copy of the GNU General Public License
##    along with this program.  If not, see <http://www.gnu.org/licenses/>.
##
###############################################################################

from osv import fields, osv
import netsvc
import datetime

class stock_move(osv.osv):
    
    _inherit = "stock.move"

    def action_done(self, cr, uid, ids, context=None):
        # auto generate customer invoice of  if the stock move is to the customer and the customers sale order has been satisfied
        res = super(stock_move, self).action_done(cr, uid, ids, context=context)
        return res
        stock_move_obj = self.pool.get('stock.move')
        sale_order_obj = self.pool.get('sale.order')
        stock_picking_obj = self.pool.get('stock.picking')
        for stock_move_item in stock_move_obj.browse(cr, uid, ids):
            # i'm assuming that the sale_line_id will be carried over if a delivery is split, need to check to see if this is the case
            if stock_move_item.sale_line_id:
                sale_order = sale_order_obj.browse(cr, uid, stock_move_item.sale_line_id)
                if sale_order.order_policy == 'automatic':
                    if not sale_order.invoice_quantity == 'procurement':
                        print 'the invoice_quantity should be procurement. It\'s been changed, hunt it down and destroy'
                    journal_id = 9 # sale_journal. check to see if this is the right journal
                    context['inv_type'] = stock_picking_obj._get_invoice_type(stock_picking_obj.browse(cr, uid, stock_move_item.picking_id))
                    context['date_inv'] = datetime.datetime.now().strftime("%Y-%m-%d")
                    stock_picking_obj.action_invoice_create(cr, uid, [stock_move_item.picking_id.id], journal_id=journal_id, context=context)
            if stock_move_item.production_id:
                ratio = stock_move_item.product_qty / stock_move_item.production_id.product_qty
                # will only need to change sekf back to what it was if i include the raw material invoice creation in this function
                old_self = self
                self = self.pool.get('purchase.order')
                purchase_order_ids = self.pool.get('purchase.order').search(cr, uid,[('origin','like',stock_move_item.production_id.name)])
                invoice_id = self.action_invoice_create(cr, uid, purchase_order_ids, {})
                self = old_self
                invoice_line_ids = self.pool.get('account.invoice.line').search(cr, uid, [('invoice_id','=', invoice_id)])
                stock_move_item.production_id.product_lines[0].product_id.id
                for production_line in stock_move_item.production_id.product_lines:
                    for invoice_line in self.pool.get('account.invoice.line').browse(cr, uid, invoice_line_ids):
                        if production_line.product_id == invoice_line.product_id:
                            self.pool.get('account.invoice.line').write(cr, uid, invoice_line.id,{'quantity':ratio * production_line.product_qty})
        return True


    def check_prodlot_field(self, cr, uid, ids, context):
        # If the prodlot field is empty open the new prodlot wizard
        for stock_move in self.pool.get('stock.move').browse(cr, uid, ids):
            if stock_move.prodlot_id:
                raise osv.except_osv('No Action Taken','There is already a production lot assigned')
                return False
            else:
                return {
                    'name':("New Production Lot"),
                    'view_mode': 'form',
                    'view_id': False,
                    'view_type': 'form',
                    'res_model': 'wiz.new.prodlot',
                    'res_id': False,
                    'type': 'ir.actions.act_window',
                    'nodestroy': True,
                    'target': 'new',
                    'domain': '[]',
                    'context': dict(context, active_ids=ids)
                }

    def new_prod_lot(self, cr, uid, ids, context):
        # add's a new production lot to a stock move
        move_obj = self.pool.get('stock.move')
        for move in move_obj.browse(cr, uid, ids):
            if not move.prodlot_id:
                prodlot_obj = self.pool.get('stock.production.lot')
                seq_obj = self.pool.get('ir.sequence')
                if context['prodlot_name'] == False:
                    prodlot_name = seq_obj.get(cr,uid, 'stock.lot.serial')
                else:
                    prodlot_name = context['prodlot_name']
                prodlot_id = prodlot_obj.create(cr, uid, {
                    'product_id': move.product_id.id,
                    'name': prodlot_name
                    })
                move_obj.write(cr, uid, move.id, {'prodlot_id':prodlot_id}, context)
            else:
                raise osv.except_osv('No Action Taken', 'The production lot is already assigned')
        return True

    def fifo(self, cr, uid, ids, context):
        # assigns the oldest available production lot if one is available
        move_obj = self.pool.get('stock.move')
        move_item = move_obj.browse(cr,uid,ids[0]) # for the sake of convention I should really do this with a loop
        if not move_item.prodlot_id.id:
            prodlot_obj = self.pool.get('stock.production.lot')
            prodlots = prodlot_obj.search(cr, uid, [('product_id','=',move_item.product_id.id),('stock_available','>',0)], order = 'create_date')
            if prodlots:
                available_stock = 0
                for prodlot in prodlots:
                    if prodlot_obj._get_stock(cr, uid, prodlot, prodlot, context)[prodlot] > move_item.product_qty:
                        move_obj.write(cr, uid, move_item.id, {'prodlot_id': prodlot}, context)
                        return True
                    else:
                        available_stock += prodlot_obj._get_stock(cr, uid, prodlot, prodlot, context)[prodlot]
                if available_stock > move_item.product_qty:
                    raise osv.except_osv('Split Required','There are enough production lots available but the stock move will need to be split')
                    return False
                else:
                    raise osv.except_osv('Not Enough Stock','There is only %s in production lots assign to:\n%s' % (available_stock, move_item.product_id.name))
                    return False
            else:
                raise osv.except_osv('No Production Lots', 'There are no production lots available for:\n%s' % move_item.product_id.name)
                return False
        else:
            raise osv.except_osv('No Action Taken', 'The production lot is already assigned')
            return False

stock_move()
