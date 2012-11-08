from osv import osv,fields
import time

class sale_damagelog(osv.osv):

    _name = 'sale.damagelog'
    _rec_name = 'name'
    
    def _get_attachments_count(self, cr, uid, ids, name, arg, context={}):
        res = {}
        attachment_obj = self.pool.get('ir.attachment')
        for id in ids: 
            res[id] = len(attachment_obj.search(cr, uid, [('res_id','=',id),('res_model','=','sale.damagelog')], context=context))
        return res
    
    def _get_name(self, cr, uid, ids, name, arg, context={}):
        res = {}
        for id in ids: 
            res[id] = 'LOG%06d' % (id,)
        return res
    
    def check_qty(self, cr, uid, ids, parent=None):
        damage_rec = self.browse(cr, uid, ids[0])
        if damage_rec.product_qty <= 0 or damage_rec.product_qty > damage_rec.stock_move_id.product_qty:
            return False
        return True
    
    _columns = {
                'name':fields.function(_get_name,method=True,type='char',string='Name',store=True),
                'ticket_id':fields.char('Ticket ID',size=16),
                'stock_move_id':fields.many2one('stock.move', 'Stock Move', required=True),
                'sale_line_id':fields.related('stock_move_id','sale_line_id',type='many2one',relation='sale.order.line',string='Sale Order Line', readonly=True),
                'sale_order_id':fields.related('sale_line_id', 'order_id', type='many2one', relation='sale.order',string='Order Reference', readonly=True),
                'partner_id':fields.related('sale_order_id', 'partner_id', type='many2one', relation='res.partner',string='Customer', readonly=True, store=True),
                'product_id':fields.related('stock_move_id', 'product_id', type='many2one', relation='product.product',string='Product', readonly=True, store=True),
                'product_sku': fields.related('product_id', 'default_code',type='char',size=16, string='Product Code', readonly=True),
                'dispatch_date' : fields.related('stock_move_id', 'date', type='datetime', string='Dispatch Date',readonly=True, store=True),
                'date_order' : fields.related('sale_order_id', 'date_order', type='datetime', string='Order Date',readonly=True, store=True),
                'log_date':fields.datetime('Date Created', readonly=True),
                'log_uid':fields.many2one('res.users','Created By', readonly=True),
                'claim_ids':fields.one2many('crm.claim','damagelog_id','Claims'),
                'customer_refund_id':fields.many2one('account.invoice','Customer Refund'),
                'customer_refund_amount':fields.related('customer_refund_id','amount_total',type='float',string='Refund Amount'),
                'issue_description':fields.text('Comments'),
                'num_attachments':fields.function(_get_attachments_count,method=True,type='integer',string='#Attachments'),
                'category':fields.selection([('pre_delay','Pre-dispatch / Delay'),
                                            ('pre_cancel', 'Pre-dispatch / General cancellation'),
                                            ('del_cancel', 'Delivery / Cancellation'),
                                            ('del_undel', 'Delivery / Item undelivered due to size'),
                                            ('pd_quality', 'Post-delivery / Quality issue'),
                                            ('pd_damage', 'Post-delivery / Delivery damage (product)'),
                                            ('pd_mess', 'Post-delivery / Delivery mess-ups (service)'),
                                            ('pd_return', 'Post-delivery / General return'),
                                            ('fraud', 'Fraud & Chargebacks'),
                                            ('voucher', 'Vouchers not applied/Double order'),
                                            ('other', 'IT/Test orders/Other')], 'Category', required=True),
                'product_supplier':fields.many2one('res.partner','Product Supplier'),
                'product_qty':fields.float('Qty'),
                'product_uom':fields.many2one('product.uom','UoM', required=True),
                'comprequest_ids': fields.one2many('sale.comprequest', 'damagelog_id', 'Compensation Requests'), # is this really right?
                }
    
    _defaults = {
                 'log_date':lambda *a : time.strftime('%Y-%m-%d %H:%M:%S'),
                 'log_uid': lambda self,cr,uid,ctx : uid,
                 }
    
    _constraints = [
        (check_qty, 'You can not have product quantity greater than shipped quantity and It should have a positive value!', ['product_qty'])
    ]

    
    def onchange_stock_move(self, cr, uid, ids, stock_move_id):
        value = {}
        if stock_move_id:
            stock_move_rec = self.pool.get('stock.move').browse(cr, uid, stock_move_id)
            value['sale_order_id'] = stock_move_rec.sale_line_id.order_id.id or False
            value['product_id'] =  stock_move_rec.product_id.id
            value['product_sku'] =  stock_move_rec.product_id.default_code
            value['product_uom'] = stock_move_rec.product_uom.id
            value['product_qty'] = stock_move_rec.product_qty
            value['product_supplier'] = stock_move_rec.product_id.seller_ids and stock_move_rec.product_id.seller_ids[0].name.id or False
            value['sale_line_id'] = stock_move_rec.sale_line_id.id
            value['dispatch_date'] = stock_move_rec.date
            value['partner_id'] = stock_move_rec.sale_line_id.order_id.partner_id.id or False
        return {'value':value}
    
    def create_refund(self, cr, uid, ids, context=None):
        return # Deprecated
        if context is None:
            context = {}
        invoice_obj = self.pool.get('account.invoice')
        inv_line_obj = self.pool.get('account.invoice.line')
        damagelog_rec = self.browse(cr,uid,ids,context=context)[0]
        prod_acc_property =  damagelog_rec.product_id.property_account_income.id or damagelog_rec.product_id.categ_id.property_account_income_categ.id
        prod_acc_id = self.pool.get('account.fiscal.position').map_account(cr, uid, False, prod_acc_property)
        refund_line_vals = {
                            'product_id':damagelog_rec.product_id.id,
                            'uos_id':damagelog_rec.product_uom.id,
                            'quantity':damagelog_rec.product_qty,
                            'price_unit':damagelog_rec.product_id.list_price,
                            'name':'[' + damagelog_rec.product_sku or ' ' + ']' + damagelog_rec.product_id.name,
                            'account_id': prod_acc_id  
                           }
        inv_line_id = inv_line_obj.create(cr, uid, refund_line_vals, context=context)
        partner_acc_property = damagelog_rec.partner_id.property_account_receivable.id
        partner_acc_id = self.pool.get('account.fiscal.position').map_account(cr, uid, False, partner_acc_property)
        refund_vals = {
                        'partner_id':damagelog_rec.partner_id.id,
                        'address_invoice_id':damagelog_rec.sale_order_id.partner_invoice_id.id,
                        'account_id':partner_acc_id,
                        'type':'out_refund',
                        'invoice_line':[(6,0,[inv_line_id])],
                        'name':'Refund:%s' % (damagelog_rec.sale_order_id.name),
                      }
        
        inv_id = invoice_obj.create(cr, uid, refund_vals, context=context)
        self.write(cr, uid, ids, {'customer_refund_id':inv_id}, context=context)
        return {}

sale_damagelog()


class crm_claim(osv.osv):
    
    _inherit = 'crm.claim'
    
    _columns = {
                'damagelog_id':fields.many2one('sale.damagelog','Issue Log'),
                }
    
crm_claim()

