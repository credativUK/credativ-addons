from osv import osv,fields
import time

class sale_comprequest(osv.osv):
    _name = 'sale.comprequest'

    _columns = {
        'name' : fields.char('Name', size=128, required=True),
        'create_date': fields.datetime('Date Created', readonly=True),
        'create_uid': fields.many2one('res.users', 'Created By', readonly=True),
        'write_date': fields.datetime('Last Updated', readonly=True),
        'write_uid': fields.many2one('res.users', 'Last Updated By', readonly=True),
        'cancel_date': fields.datetime('Last Updated', readonly=True),
        'cancel_uid': fields.many2one('res.users', 'Last Updated By', readonly=True),
        'confirm_date': fields.datetime('Last Updated', readonly=True),
        'confirm_uid': fields.many2one('res.users', 'Last Updated By', readonly=True),
        'sale_order_id': fields.many2one('sale.order', 'Order Reference', readonly=True, states={'draft': [('readonly', False)]}),
        'date_order': fields.related('sale_order_id', 'date_order', type='date', string='Order Date', readonly=True),
        'partner_id': fields.related('sale_order_id', 'partner_id', type='many2one', relation='res.partner', string='Partner', readonly=True),
        'refund_type': fields.selection(
            [('refund', 'Refund'), ('voucher', 'Voucher'),
             ('replace-same', 'Replacement - same'),
             ('replace-diff', 'Replacement - different'),
             ('redispatch', 'Redispatch')], 'Compensation Type', required=True, readonly=True, states={'draft': [('readonly', False)]}),
        'refund_value': fields.float('Compensation Value', readonly=True, states={'draft': [('readonly', False)]}),
        'state': fields.selection([('draft', 'Draft'), ('processing', 'Processing'), ('confirmed', 'Confirmed'), ('cancel', 'Cancelled')], 'Compensation Status', required=True, readonly=True),
        'voucher_code': fields.char('Voucher Code', size=200, readonly=True, states={'draft': [('readonly', False)]}),
        'repl_order_ref': fields.many2one('sale.order', 'Rpl/Red Order Ref', readonly=True, states={'draft': [('readonly', False)]}),
        'comment_ids': fields.one2many('sale.comprequest.comment', 'comprequest_id'),
        'notes': fields.text('Notes'),
        'damagelog_ids': fields.one2many('sale.damagelog', 'comprequest_id', string='Issues', required=True, readonly=True, states={'draft': [('readonly', False)]}),
    }

    def _check_refund_amount(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        if isinstance(ids, (list, tuple)):
            ids = ids[0]

        this = self.browse(cr, uid, ids, context=context)
        other_comprequests = self.pool.get('sale.comprequest').search(cr, uid, [('sale_order_id','=',this.sale_order_id),
                                                                                ('id','<>',ids),
                                                                                ('refund_type','in',['refund','voucher'])], context=context)
        refunded = sum([c.refund_value for c in self.pool.get('sale.comprequest').browse(cr, uid, other_comprequests, context=context)])
        return this.refund_value < refunded

    _constraints = [
        (_check_refund_amount, 'This refund amount would make the total refunded greater than the order totel.', ['refund_value']),
        ]

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
    
    def action_cancel(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'cancel', 'cancel_uid': uid, 'cancel_date': time.strftime('%Y-%m-%d %H:%M:%S')}, context=context)

    def action_draft(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'draft'}, context=context)
        # TODO Trigger email to reporting agent

    def action_process(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'processing'}, context=context)

    def action_confirm(self, cr, uid, ids, context=None):
        comp_reqs = self.browse(cr, uid, ids, context=context)
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
        self.write(cr, uid, ids, {'state': 'confirmed', 'confirm_uid': uid, 'confirm_date': time.strftime('%Y-%m-%d %H:%M:%S')}, context=context)

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


class sale_order_line(osv.osv):
    _inherit = 'sale.order.line'

    def _get_latest_compensation(self, cr, uid, ids, name, arg, context=None):
        if context is None:
            context = {}

        res = {}
        dl_pool = self.pool.get('sale.damagelog')
        cr_pool = self.pool.get('sale.comprequest')

        for id in ids:
            # FIXME Why is this taking three steps?
            damagelog_ids = dl_pool.search(cr, uid, [('sale_line_id','=',id)], context=context)
            comprequest_ids = [r['comprequest_id'] for r in dl_pool.read(cr, uid, damagelog_ids, ['comprequest_id'])]
            # FIXME This should probably show returns and replacements too
            comprequest_id = cr_pool.search(cr, uid, [('id','in',comprequest_ids),
                                                      ('state','<>','cancel'),
                                                      ('refund_type','in',['refund','voucher'])],
                                            limit=1, order='write_date', context=context)
            if comprequest_id:
                comprequest = cr_pool.browse(cr, uid, comprequest_id, context=context)
                res[id] = '%s: %.2f (%s)' % (comprequest.refund_type, comprequest.refund_value, comprequest.state)
            else:
                res[id] = None

        return res

    _columns = {
        'compensation': fields.function(_get_latest_compensation, string='Compensation'),
        }

sale_order_line()


class sale_damagelog_from_order_lines(osv.osv_memory):
    _name = 'sale.damagelog.from.order.lines'
    _description = 'Select sale order lines to log issues against'
    _columns = {
        'line_ids': fields.one2many('sale.order.line', 'order_id', 'Order Lines'),
        }

    def add_lines(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        order_id = context.get('order_id', False)
        if not order_id:
            return {'type': 'ir.actions.act_window_close'}
        data =  self.read(cr, uid, ids, context=context)[0]
        line_ids = data['line_ids']
        if not line_ids:
            return {'type': 'ir.actions.act_window_close'}

        

sale_damagelog_from_order_lines()
