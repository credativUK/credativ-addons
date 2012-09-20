from osv import osv,fields
import time

class sale_comprequest(osv.osv):
    _name = 'sale.comprequest'

    _columns = {
        'name' : fields.char('Name', size=128, required=True),
        'damagelog_id': fields.many2one('sale.damagelog', 'Issue Log', required=True, readonly=True, states={'draft': [('readonly', False)]}),
        'create_date': fields.datetime('Date Created', readonly=True),
        'create_uid': fields.many2one('res.users', 'Created By', readonly=True),
        'write_date': fields.datetime('Last Updated', readonly=True),
        'write_uid': fields.many2one('res.users', 'Last Updated By', readonly=True),
        'cancel_date': fields.datetime('Last Updated', readonly=True),
        'cancel_uid': fields.many2one('res.users', 'Last Updated By', readonly=True),
        'confirm_date': fields.datetime('Last Updated', readonly=True),
        'confirm_uid': fields.many2one('res.users', 'Last Updated By', readonly=True),
        'sale_order_id': fields.related('damagelog_id', 'stock_move_id', 'sale_line_id', 'order_id', type='many2one', relation='sale.order', string='Order Reference', readonly=True, store=True),
        'date_order': fields.related('sale_order_id', 'date_order', type='date', string='Order Date', readonly=True),
        'product_id': fields.related('damagelog_id', 'stock_move_id', 'product_id', type='many2one', relation='product.product', string='Product', readonly=True),
        'product_sku': fields.related('product_id', 'default_code', type='char', size=16, string='Product Code', readonly=True),
        'product_value': fields.float('Product Value', readonly=True),
        'product_supplier': fields.related('damagelog_id', 'product_supplier', type='many2one', relation='res.partner', string='Product Supplier', readonly=True),
        'partner_id': fields.related('sale_order_id', 'partner_id', type='many2one', relation='res.partner', string='Partner', readonly=True),
        'refund_type': fields.selection(
            [('refund', 'Refund'), ('voucher', 'Voucher'),
             ('replace-same', 'Replacement - same'),
             ('replace-diff', 'Replacement - different'),
             ('redispatch', 'Redispatch')], 'Compensation Type', required=True, readonly=True, states={'draft': [('readonly', False)]}),
        'refund_value': fields.float('Compensation Value', readonly=True, states={'draft': [('readonly', False)]}),
        'state': fields.selection([('draft', 'Draft'), ('confirmed', 'Confirmed'), ('cancel', 'Cancelled')], 'Compensation Status', required=True, readonly=True),
        'voucher_code': fields.char('Voucher Code', size=200, readonly=True, states={'draft': [('readonly', False)]}),
        'repl_order_ref': fields.many2one('sale.order', 'Replacement / Redispatch Order Reference', readonly=True, states={'draft': [('readonly', False)]}),
        'comment_ids': fields.one2many('sale.comprequest.comment', 'comprequest_id'),
        'notes': fields.text('Notes'),
    }
    
    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'Compensation Request name must be unique !'),
    ]
    _order = 'name desc'
    
    _defaults = {
        'name': lambda obj, cr, uid, context: obj.pool.get('ir.sequence').get(cr, uid, 'sale.comprequest'),
        'state': lambda *a: 'draft',
    }

    def onchange_damagelog_id(self, cr, uid, ids, damagelog_id):
        value = {}
        if damagelog_id:
            damagelog_rec = self.pool.get('sale.damagelog').browse(cr, uid, damagelog_id)
            value['sale_order_id'] = damagelog_rec.sale_order_id.id
            value['partner_id'] = damagelog_rec.sale_order_id.partner_id.id
            value['product_id'] =  damagelog_rec.product_id.id
            value['product_sku'] =  damagelog_rec.product_sku
            value['product_supplier'] = damagelog_rec.product_supplier.id
            value['product_value'] = damagelog_rec.product_id.list_price
        return {'value':value}
    
    def action_cancel(self, cr, uid, ids, *args):
        self.write(cr, uid, ids, {'state': 'cancel', 'cancel_uid': uid, 'cancel_date': time.strftime('%Y-%m-%d %H:%M:%S')}, context=None)

    def action_draft(self, cr, uid, ids, *args):
        self.write(cr, uid, ids, {'state': 'draft'}, context=None)

    def action_confirm(self, cr, uid, ids, *args):
        comp_reqs = self.browse(cr, uid, ids, context=None)
        raise_errors = []
        for comp_req in comp_reqs:
            if comp_req.refund_type in ('replace-same', 'replace-diff', 'redispatch') and not comp_req.repl_order_ref:
                raise_text = 'Replacement / Redispatch Order Reference is required for this Compensation type in record %s' % (comp_req.name or '',)
                raise_errors.append(raise_text)
            if comp_req.refund_type == 'voucher' and not comp_req.voucher_code:
                raise_text = 'Voucher Code is required for this Compensation type in record %s' % (comp_req.name or '',)
                raise_errors.append(raise_text)
            if comp_req.refund_type in ('refund', 'voucher') and not comp_req.refund_value:
                raise_text = 'Compensation Value is required for this Compensation type in record %s' % (comp_req.name or '',)
                raise_errors.append(raise_text)
        if raise_errors:
            raise osv.except_osv('User Error', '\n\n'.join(raise_errors)) # raise_errors is a list of strings
        self.write(cr, uid, ids, {'state': 'confirmed', 'confirm_uid': uid, 'confirm_date': time.strftime('%Y-%m-%d %H:%M:%S')}, context=None)

sale_comprequest()


class sale_comprequest_comment(osv.osv):

    _name = 'sale.comprequest.comment'
    _rec_name = 'id'

    _columns = {
        'comprequest_id': fields.many2one('sale.comprequest', 'Compensation Request', required=True),
        'create_date': fields.datetime('Date Created', readonly=True),
        'create_uid': fields.many2one('res.users', 'Created By', readonly=True),
        'comment': fields.text('Comment'),
    }

sale_comprequest_comment()

class sale_order(osv.osv):
    _inherit = 'sale.order'
    
    _columns = {
        'comp_reqs': fields.one2many('sale.comprequest', 'sale_order_id', 'Compensation Requests', readonly=True),
        }

sale_order()
