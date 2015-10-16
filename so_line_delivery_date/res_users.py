from openerp.osv import osv, fields

class res_users(osv.osv):

    _inherit = 'res.users'

    def create(self, cr, uid, vals, context=None):
        res = super(res_users, self).create(cr, uid, vals, context=context)
        if res:
            com = vals.get('company_id', False)
            if com:
                com_browse = self.pool.get('res.company').browse(cr, uid, com, context=context)
                if com_browse.delivery_date_per_line:
                    group_pool = self.pool.get('res.groups')
                    gid = group_pool.search(cr, uid, [('name','=','Delivery dates per-line')], context=context)
                    if gid:
                        group_pool.write(cr, uid, gid, {'users':[(4, res)]}, context=context)
        return res
