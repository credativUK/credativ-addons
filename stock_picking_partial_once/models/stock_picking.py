# -*- coding: utf-8 -*-
# (c) 2016 credativ ltd. - Ondřej Kuzník
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp.osv import orm

class StockPicking(orm.Model):
    _inherit = 'stock.picking'

    def copy(self, cr, uid, id, default=None, context=None):
        default = (default or {}).copy()

        picking = self.browse(cr, uid, id, context=context)
        if picking.type == 'out':
            default['move_type'] = 'one'

        return super(StockPicking, self).copy(cr, uid, id, default, context=context)

    def do_partial(self, cr, uid, ids, partial_datas, context=None):
        res = super(StockPicking, self).do_partial(cr, uid, ids, partial_datas, context=context)
        for picking in self.browse(cr, uid, ids, context=context):
            # if the picking is still not done, switch to "All at once"
            if picking.type == 'out' \
                    and picking.move_type == 'direct' \
                    and picking.state not in ('done', 'cancel'):
                picking.write({'move_type': 'one'})
        return res

class StockPickingOut(orm.Model):
    _inherit = 'stock.picking.out'

    def copy(self, cr, uid, id, default=None, context=None):
        default = (default or {}).copy()
        default['move_type'] = 'one'
        return super(StockPickingOut, self).copy(cr, uid, id, default, context=context)

    def do_partial(self, cr, uid, ids, partial_datas, context=None):
        res = super(StockPickingOut, self).do_partial(cr, uid, ids, partial_datas, context=context)
        for picking in self.browse(cr, uid, ids, context=context):
            # if the picking is still not done, switch to "All at once"
            if picking.move_type == 'direct' and picking.state not in ('done', 'cancel'):
                picking.write({'move_type': 'one'})
        return res
