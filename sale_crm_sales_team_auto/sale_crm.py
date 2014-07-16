from osv import osv, fields


class sale_order(osv.osv):

    _name    = 'sale.order'
    _inherit = 'sale.order'


    def _get_section_id(self, cr, uid, part, context=None):
        partner_obj  = self.pool.get('res.partner')
        partner_data = partner_obj.read(cr, uid, part, ['section_id'], context=context)
        section_id = partner_data['section_id'] and partner_data['section_id'][0] or False
        return section_id


    def onchange_partner_id(self, cr, uid, ids, part, context=None):
        res = super(sale_order, self).onchange_partner_id(cr, uid, ids, part, context=context)
        val = res.get('value') or {}
        section_id = self._get_section_id(cr, uid, part, context=context)
        val.update({'section_id' : section_id})
        res.update({'value' : val})
        return res
        

    def default_get(self, cr, uid, fields, context=None):
        res = super(sale_order, self).default_get(cr, uid, fields, context=context)
        part = res.get('partner_id', False)
        if part:
            res.update({'section_id' : self._get_section_id(cr, uid, part, context=context)})
        return res



sale_order()
