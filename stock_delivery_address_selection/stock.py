# -*- encoding: utf-8 -*- 
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2014 credativ Ltd (<http://credativ.co.uk>).
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################


from openerp.osv import osv, fields



class StockPicking(osv.Model):

    # Due to questionable behaviour of the osv's class inheritance system, the new fields
    # on stock.picking.out need to be duplicated for stock.picking.in and stock.picking.
    # This duplication is seen in some core modules.
    # Defining _name and _table as follows (as per the original stock_picking_out definition)
    # seems to sidestep the issue, however it isn't completely clear that there won't be any
    # side-effects, so we've elected to go for the possibly safer code duplication approach.

    #_name='stock.picking.out'
    #_table='stock_picking'

    _inherit = 'stock.picking'
    

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
        elif ids:
            # Generate a pseudo-read-result if we need to use a partner_id
            # other than the one currently stored on the record (e.g. in an
            # onchange method since the write hasn't happened yet).
            [ptnrs.append({'id' : id, 'partner_id' : [partner_id]}) for id in ids]
        else:
            ptnrs = [{'id' : '', 'partner_id' : [partner_id]}]
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
        res = super(StockPicking, self).onchange_partner_in(cr, uid, ids, partner_id=partner_id, context=context)
        rel_adds = []
        res['value'] = res.get('value', {})
        if partner_id:
            rel_adds = self._calc_related_addresses(cr, uid, ids, None, None, partner_id=partner_id, context=context)
            if ids:
                rel_adds = rel_adds[ids[0]]
            else:
                rel_adds = rel_adds['']
        res['value'].update({'related_addresses' : rel_adds, 'partner_id' : delivery_address})
        return res


    def onchange_delivery_address(self, cr, uid, ids, partner_id=False, main_partner_id=False, move_lines=None, context=None):
        res = {'value' : {}}
        new_delivery_addr = partner_id or main_partner_id or False
        if new_delivery_addr != partner_id:
            res['value'].update({'partner_id' : new_delivery_addr})
        if not move_lines:
            return res
        res['value'].update({'move_lines' : []})
        for move_tuple in move_lines:
            if move_tuple[0] == 0:          # New line
                new_vals = move_tuple[2]
                new_vals.update({'partner_id' : new_delivery_addr})
                res['value']['move_lines'].append((0, 0, new_vals))
            elif move_tuple[0] in (1,4):    # Existing line
                move_id = move_tuple[1]
                new_vals = {'partner_id' : new_delivery_addr}
                res['value']['move_lines'].append((1, move_id, new_vals))
            else:
                res['value']['move_lines'].append(move_tuple)
        return res


    def create(self, cr, uid, vals, context=None):
        ptnr_main_id = vals.get('main_partner_id')
        ptnr_id = vals.get('partner_id')
        if not ptnr_main_id and ptnr_id:
            vals.update({'main_partner_id' : ptnr_id})
        return super(StockPicking, self).create(cr, uid, vals, context=context)



    _columns = {
            'main_partner_id' : fields.many2one('res.partner', 'Customer', help='Address to which the products will be delivered.'),
            'related_addresses' : fields.function(_calc_related_addresses, type='many2many', relation='res.partner'),
    }




class StockPickingOut(osv.Model):

    _inherit = 'stock.picking.out'


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
        elif ids:
            # Generate a pseudo-read-result if we need to use a partner_id
            # other than the one currently stored on the record (e.g. in an
            # onchange method since the write hasn't happened yet).
            [ptnrs.append({'id' : id, 'partner_id' : [partner_id]}) for id in ids]
        else:
            ptnrs = [{'id' : '', 'partner_id' : [partner_id]}]
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
        res = super(StockPickingOut, self).onchange_partner_in(cr, uid, ids, partner_id=partner_id, context=context)
        rel_adds = []
        res['value'] = res.get('value', {})
        delivery_address = False
        if partner_id:
            delivery_address = partner_id
            rel_adds = self._calc_related_addresses(cr, uid, ids, None, None, partner_id=partner_id, context=context)
            if ids:
                rel_adds = rel_adds[ids[0]]
            else:
                rel_adds = rel_adds['']
        res['value'].update({'related_addresses' : rel_adds, 'partner_id' : delivery_address})
        return res


    def onchange_delivery_address(self, cr, uid, ids, partner_id=False, main_partner_id=False, move_lines=None, context=None):
        res = {'value' : {}}
        new_delivery_addr = partner_id or main_partner_id or False
        if new_delivery_addr != partner_id:
            res['value'].update({'partner_id' : new_delivery_addr})
        if not move_lines:
            return res
        res['value'].update({'move_lines' : []})
        for move_tuple in move_lines:
            if move_tuple[0] == 0:          # New line
                new_vals = move_tuple[2]
                new_vals.update({'partner_id' : new_delivery_addr})
                res['value']['move_lines'].append((0, 0, new_vals))
            elif move_tuple[0] in (1,4):    # Existing line
                move_id = move_tuple[1]
                new_vals = {'partner_id' : new_delivery_addr}
                res['value']['move_lines'].append((1, move_id, new_vals))
            else:
                res['value']['move_lines'].append(move_tuple)
        return res


    def create(self, cr, uid, vals, context=None):
        ptnr_main_id = vals.get('main_partner_id')
        ptnr_id = vals.get('partner_id')
        if not ptnr_main_id and ptnr_id:
            vals.update({'main_partner_id' : ptnr_id})
        return super(StockPickingOut, self).create(cr, uid, vals, context=context)



    _columns = {
            'main_partner_id' : fields.many2one('res.partner', 'Customer', help='Address to which the products will be delivered.'),
            'related_addresses' : fields.function(_calc_related_addresses, type='many2many', relation='res.partner'),
    }

