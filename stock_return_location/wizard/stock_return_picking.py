from osv import osv, fields


class stock_return_picking_memory(osv.osv_memory):

    _name    = 'stock.return.picking.memory'
    _inherit = 'stock.return.picking.memory'

    _columns = {
            'location_dest_id' : fields.many2one('stock.location', 'Destination Location', required=True, help="Location to which the system will move the stock."),
    }


stock_return_picking_memory()




class stock_return_picking(osv.osv_memory):

    _name    = 'stock.return.picking'
    _inherit = 'stock.return.picking'


    def create_returns(self, cr, uid, ids, context=None):
        move_obj = self.pool.get('stock.move')
        mem_obj  = self.pool.get('stock.return.picking.memory')
        ret = super(stock_return_picking, self).create_returns(cr, uid, ids, context=context)
        prm_datas = self.read(cr, uid, ids, ['product_return_moves'], context=context)
        for prm_data in prm_datas:
            mem_ids = prm_data['product_return_moves']
            mem_data = mem_obj.read(cr, uid, mem_ids, ['move_id', 'location_dest_id'], context=context)
            move_to_dest = {}
            for data in mem_data:
                move_to_dest.update({data['move_id'][0] : data['location_dest_id'][0]})
            move_ids = [mem['move_id'][0] for mem in mem_data]
            move_datas = move_obj.read(cr, uid, move_ids, ['location_dest_id','move_history_ids2'], context=context)
            for move_data in move_datas:
                new_move_ids = move_data['move_history_ids2']
                for new_move_id in new_move_ids:
                    move_id = move_data['id']
                    move_obj.write(cr, uid, new_move_id, {'location_dest_id' : move_to_dest[move_id]}, context=context)
        return ret


    def default_get(self, cr, uid, fields, context=None):
        move_obj = self.pool.get('stock.move')
        res = super(stock_return_picking, self).default_get(cr, uid, fields, context=context)
        moves = res.get('product_return_moves') or []
        new_moves = []
        for move in moves:
            mid = move.get('move_id')
            if mid:
                dst = move_obj.read(cr, uid, mid, ['location_id'], context=context)['location_id']
                move.update({'location_dest_id' : dst and dst[0] or False})
            new_moves.append(move)
        res.update({'product_return_moves' : new_moves})
        return res


stock_return_picking()
