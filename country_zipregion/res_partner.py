# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2012 credativ Ltd (<http://credativ.co.uk>).
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
from util import _get_zipregion_group_names

class res_partner_address(osv.osv):
    _inherit = 'res.partner.address'

    def search(self, cr, user, args, offset=0, limit=None, order=None, context=None, count=False):
        newargs, ids = [], []
        for arg in args:
            if arg[0] == 'region_group_id_select':
                cr.execute("""SELECT rpa.id FROM res_partner_address rpa
                    INNER JOIN res_zip_region zr ON zr.country_id = rpa.country_id AND COALESCE(rpa.zip, '') ~* COALESCE(zr.zip_regex, '')
                    INNER JOIN res_zip_region_rel zrr ON zrr.region_id = zr.id
                    INNER JOIN res_zip_region_group zrg ON zrr.region_group_id = zrg.id
                    WHERE zrg.id = %s GROUP BY rpa.id""", (arg[2],))
                ids = map(lambda x:x[0], cr.fetchall())
                if ids: newargs.append(('id', 'in', ids))
                else: newargs.append(('id', 'in', [0]))
            else:
                newargs.append(arg)
        return super(res_partner_address, self).search(cr, user, newargs, offset=offset, limit=limit, order=order, context=context, count=count)
    
    def _get_zipregion_group_ids(self, cr, uid, ids, fields, arg, context=None):
        res = {}
        for id in ids:
            res[id] = {}
            for field in fields:
                if field == 'region_group_ids':
                    res[id][field] = []
                elif field == 'region_group_names':
                    res[id][field] = ''
        
        cr.execute("""
            SELECT rpa.id, zrg.id, zrg.name FROM res_partner_address rpa
            INNER JOIN res_zip_region zr ON zr.country_id = rpa.country_id AND COALESCE(rpa.zip, '') ~* COALESCE(zr.zip_regex, '')
            INNER JOIN res_zip_region_rel zrr ON zrr.region_id = zr.id
            INNER JOIN res_zip_region_group zrg ON zrr.region_group_id = zrg.id
            WHERE rpa.id in %s GROUP BY rpa.id, zrg.id, zrg.name
            ORDER BY zrg.id""", (tuple(ids),))
        data = cr.fetchall()
        
        for address_id, zonegroup_id, zonegroup_name in data:
            if 'region_group_ids' in fields:
                res[address_id]['region_group_ids'].append(zonegroup_id)
            if 'region_group_names' in fields:
                sep = ''
                if len(res[address_id]['region_group_names']) > 0: sep = ', '
                res[address_id]['region_group_names'] = "%s%s%s" % (res[address_id]['region_group_names'], sep, zonegroup_name,)
        
        return res

    _columns = {
        'region_group_ids': fields.function(_get_zipregion_group_ids, method=True, type='many2many', relation="res.zip_region_group", string="Zip Region Groups", readonly=True, multi='region_group_ids'),
        'region_group_names': fields.function(_get_zipregion_group_ids, method=True, type='char', string="Zip Region Groups", readonly=True, multi='region_group_ids'),
        'region_group_id_select': fields.selection(_get_zipregion_group_names, 'Zip Region Group'),
        }

res_partner_address()

class res_partner(osv.osv):
    _inherit = 'res.partner'

    def search(self, cr, user, args, offset=0, limit=None, order=None, context=None, count=False):
        newargs, ids = [], []
        for arg in args:
            if arg[0] == 'region_group_id_select':
                cr.execute("""SELECT rpa.partner_id FROM res_partner_address rpa
                    INNER JOIN res_zip_region zr ON zr.country_id = rpa.country_id AND COALESCE(rpa.zip, '') ~* COALESCE(zr.zip_regex, '')
                    INNER JOIN res_zip_region_rel zrr ON zrr.region_id = zr.id
                    INNER JOIN res_zip_region_group zrg ON zrr.region_group_id = zrg.id
                    WHERE zrg.id = %s GROUP BY rpa.partner_id""", (arg[2],))
                ids = map(lambda x:x[0], cr.fetchall())
                if ids: newargs.append(('id', 'in', ids))
                else: newargs.append(('id', 'in', [0]))
            else:
                newargs.append(arg)
        return super(res_partner, self).search(cr, user, newargs, offset=offset, limit=limit, order=order, context=context, count=count)
    
    _columns = {
        'region_group_id_select': fields.selection(_get_zipregion_group_names, 'Zip Region Group'),
        }

res_partner()