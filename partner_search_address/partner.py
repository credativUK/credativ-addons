# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2013 credativ Ltd (<http://credativ.co.uk>).
#    All Rights Reserved
#
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

from osv import osv, fields

class res_partner(osv.osv):
    _inherit = 'res.partner'

    def name_search(self, cr, uid, name, args=None, operator='ilike', context=None, limit=100):
        if not args:
            args = []
        res = super(res_partner,self).name_search(cr, uid, name, args, operator=operator, context=context, limit=limit)
        if name and len(res) < limit:
            address = self.pool.get('res.partner.address').search(cr, uid, [('zip','ilike',name)], context=context)
            ids = self.search(cr, uid, [('address','in',address)] + args, limit=limit-len(res), context=context)
            res.extend(self.name_get(cr, uid, ids, context))
        return res

    def name_get(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        if not len(ids):
            return []
        add_obj = self.pool.get('res.partner.address')
        if context.get('show_ref'):
            res = [(r['id'], r[rec_name]) for r in self.read(cr, uid, ids, [rec_name], context)]
            return res
        else:
            res = []
            for id in ids:
                address_id = self.address_get(cr, uid, [id,]).get('default')
                partner = self.read(cr, uid, id, ['name'], context=context)
                name = [partner['name']]
                if address_id:
                    address = add_obj.read(cr, uid, address_id, ['street', 'street2', 'city', 'zip'], context=context)
                    for key in ('street', 'street2', 'city'):
                        if address[key]:
                            name.append(address[key])
                            break
                    if address['zip']:
                        name.append(address['zip'])
                res.append((id, ', '.join(name)))
            return res

res_partner()
