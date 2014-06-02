from openerp.osv import osv, fields

class so_delivery_date_configuration(osv.osv_memory):
    _inherit = 'sale.config.settings'

    _columns = {
            'delivery_date_per_line' : fields.boolean(string='Delivery dates apply per-line',
            implied_group='so_line_delivery_date.group_delivery_date_per_line',
            help='This specifies the relationship between Sale Orders and delivery dates. If set, then delivery dates are applied to Sale Order Lines rather than Sale Orders.'),
    }


    def _get_delivery_setting(self, cr, uid, context=None):
        usr = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        com = usr.company_id
        return com.delivery_date_per_line

    _defaults = {
            'delivery_date_per_line' : _get_delivery_setting,
    }

    def setup_groups(self, cr, uid, ids, company_id, operation, context=None):
        group_pool = self.pool.get('res.groups')
        gid = group_pool.search(cr, uid, [('name','=','Delivery dates per-line')], context=context)
        if gid:
            usr_pool = self.pool.get('res.users')
            usr_ids = usr_pool.search(cr, uid, [('company_id','=',company_id)], context=context)
            opcode = (operation == 'link') and 4 or 3
            for usr_id in usr_ids:
                group_pool.write(cr, uid, gid, {'users':[(opcode, usr_id)]}, context=context)


    def set_delivery_date_per_line(self, cr, uid, ids, context=None):
        config = self.browse(cr, uid, ids[0], context=context)
        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        user.company_id.write({'delivery_date_per_line' : config.delivery_date_per_line and True or False})
        group_operation = config.delivery_date_per_line and 'link' or 'unlink'
        self.setup_groups(cr, uid, ids, company_id=user.company_id.id, operation=group_operation, context=context)
