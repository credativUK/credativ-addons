from osv import osv, fields

class stock_picking_out(osv.osv):

    _name    = 'stock.picking.out'
    _inherit = 'stock.picking'
    _table   = 'stock_picking'

    

    def _get_related_addresses(self, cr, uid, ptnr_id, context=None):
        ptnr_obj = self.pool.get('res.partner')
        children = ptnr_obj.search(cr, uid, [('parent_id','=',ptnr_id)], context=context)
        grandchildren = []
        for child in children:
            grandchildren.extend(self._get_related_addresses(cr, uid, child, context=context))
        children.extend(grandchildren)
        return children



    def _find_top_level_partner(self, cr, uid, ptnr_id, context=None):
        ptnr_obj = self.pool.get('res.partner')
        parent = ptnr_obj.read(cr, uid, ptnr_id, ['parent_id'], context=context)
        if not parent['parent_id']:
            return ptnr_id
        else:
            return self._find_top_level_partner(cr, uid, parent['parent_id'][0], context=context)



    def _calc_related_addresses(self, cr, uid, ids, name, arg, context=None, partner_id=None):
        res = {}
        ptnrs = []

        if not partner_id:
            # Standard 'function field' calculation
            ptnrs = self.read(cr, uid, ids, ['partner_id'], context=context)
        else:
            # Generate a pseudo-read-result if we need to use a partner_id
            # other than the one currently stored on the record (e.g. in an
            # onchange method since the write hasn't happened yet).
            [ptnrs.append({'id' : id, 'partner_id' : [partner_id]}) for id in ids]

        for ptnr in ptnrs:
            id = ptnr['id']
            if not ptnr['partner_id']:
                res[id] = []
                continue
            tlp = self._find_top_level_partner(cr, uid, ptnr['partner_id'][0], context=context)
            res[id] = [tlp]
            res[id].extend(self._get_related_addresses(cr, uid, tlp, context=context))
        return res



    def onchange_partner_in(self, cr, uid, ids, partner_id=None, context=None):
        res = super(stock_picking_out, self).onchange_partner_in(cr, uid, ids, partner_id=partner_id, context=context)

        rel_adds = []
        res['value'] = res.get('value', {})
        if partner_id:
            rel_adds = self._calc_related_addresses(cr, uid, ids, None, None, partner_id=partner_id, context=context)[ids[0]]
        res['value'].update({'related_addresses' : rel_adds, 'delivery_address' : False})
        return res



    _columns = {
            'delivery_address' : fields.many2one('res.partner', 'Delivery Address', help='Address to which the products will be delivered.'),
            'related_addresses' : fields.function(_calc_related_addresses, type='many2many', relation='res.partner'),
    }


stock_picking_out()
