# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2014 credativ Ltd (<http://credativ.co.uk>).
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

class crm_lead(osv.osv):
    _inherit = "crm.lead"

    def search(self, cr, user, args, offset=0, limit=None, order=None, context=None, count=False):
        newargs, ids = [], []
        for arg in args:
            if arg[0] in ('region_group_id_select', 'region_group_ids'):
                if arg[1] == '=' and arg[2] == False:
                    where = "IS NULL"
                elif arg[1] == '!=' and arg[2] == False:
                    where = "IS NOT NULL"
                else:
                    where = "zrg.id = %s" % (arg[2],)
                
                cr.execute("""SELECT crm.id FROM crm_lead crm
                    LEFT OUTER JOIN res_partner_address rpa ON rpa.id = crm.partner_address_id
                    INNER JOIN res_zip_region zr ON (zr.country_id = crm.country_id AND COALESCE(crm.zip, '') ~* COALESCE(zr.zip_regex, ''))
                                                 OR (zr.country_id = rpa.country_id AND COALESCE(rpa.zip, '') ~* COALESCE(zr.zip_regex, ''))
                    INNER JOIN res_zip_region_rel zrr ON zrr.region_id = zr.id
                    INNER JOIN res_zip_region_group zrg ON zrr.region_group_id = zrg.id
                    WHERE %s GROUP BY crm.id""" % (where,))
                ids = map(lambda x:x[0], cr.fetchall())
                if ids: newargs.append(('id', 'in', ids))
                else: newargs.append(('id', 'in', [0]))
            else:
                newargs.append(arg)
        return super(crm_lead, self).search(cr, user, newargs, offset=offset, limit=limit, order=order, context=context, count=count)

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
            SELECT crm.id, zrg.id, zrg.name FROM crm_lead crm
            LEFT OUTER JOIN res_partner_address rpa ON rpa.id = crm.partner_address_id
            INNER JOIN res_zip_region zr ON (zr.country_id = crm.country_id AND COALESCE(crm.zip, '') ~* COALESCE(zr.zip_regex, ''))
                                         OR (zr.country_id = rpa.country_id AND COALESCE(rpa.zip, '') ~* COALESCE(zr.zip_regex, ''))
            INNER JOIN res_zip_region_rel zrr ON zrr.region_id = zr.id
            INNER JOIN res_zip_region_group zrg ON zrr.region_group_id = zrg.id
            WHERE crm.id in %s GROUP BY crm.id, zrg.id, zrg.name
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

    def read_group_region_group_ids(self, cr, uid, domain, fields, groupby, offset=0, limit=None, context=None, orderby=False):
        context = context or {}
        zr_obj = self.pool.get('res.zip_region_group')
        self.check_read(cr, uid)
        if not fields:
            fields = self._columns.keys()

        query = self._where_calc(cr, uid, domain, context=context)
        self._apply_ir_rules(cr, uid, query, 'read', context=context)

        fget = self.fields_get(cr, uid, fields)
        groupby_list = groupby
        group_count = group_by = 'region_group_id'
        qualified_groupby_field = '"res_zip_region_group".id'
        flist = '"res_zip_region_group".id AS region_group_id'

        aggregated_fields = [
            f for f in fields
            if f not in ('id', 'sequence')
            if fget[f]['type'] in ('integer', 'float')
            if (f in self._columns and getattr(self._columns[f], '_classic_write'))]
        for f in aggregated_fields:
            group_operator = fget[f].get('group_operator', 'sum')
            if flist:
                flist += ', '
            qualified_field = '"%s"."%s"' % (self._table, f)
            flist += "%s(%s) AS %s" % (group_operator, qualified_field, f)

        gb = groupby and (' GROUP BY ' + qualified_groupby_field) or ''

        from_clause, where_clause, where_clause_params = query.get_sql()
        where_clause = where_clause and ' WHERE ' + where_clause
        limit_str = limit and ' limit %d' % limit or ''
        offset_str = offset and ' offset %d' % offset or ''
        if len(groupby_list) < 2 and context.get('group_by_no_leaf'):
            group_count = '_'

        join_clause = ''
        if context.get('filter_by_attachments') == 'include_attachments':
            join_clause = """\nJOIN ir_attachment ia
                                ON ia.res_id = %s.id""" % self._table
            where_clause += ' AND ia.res_model = %r' % self._name
        elif context.get('filter_by_attachments') == 'exclude_attachments':
            exclude_query = """SELECT %s.id
                                FROM %s
                                JOIN ir_attachment
                                ON ir_attachment.res_id = %s.id
                                AND ir_attachment.res_model = %r""" % (self._table, self._table, self._table, self._name)
            cr.execute(exclude_query)
            exclude_ids = cr.fetchall()
            if exclude_ids and len(exclude_ids) == 1:
                where_clause += ' AND %s.id  != %s' % (self._table, exclude_ids[0])
            elif exclude_ids:
                where_clause += ' AND %s.id  not in %s' % (self._table, tuple([record_id[0] for record_id in exclude_ids]))

        join_clause += """ LEFT OUTER JOIN res_partner_address ON res_partner_address.id = crm_lead.partner_address_id
                           LEFT OUTER JOIN res_zip_region ON (res_zip_region.country_id = crm_lead.country_id AND COALESCE(crm_lead.zip, '') ~* COALESCE(res_zip_region.zip_regex, ''))
                                                          OR (res_zip_region.country_id = res_partner_address.country_id AND COALESCE(res_partner_address.zip, '') ~* COALESCE(res_zip_region.zip_regex, ''))
                           LEFT OUTER JOIN res_zip_region_rel ON res_zip_region_rel.region_id = res_zip_region.id
                           LEFT OUTER JOIN res_zip_region_group ON res_zip_region_rel.region_group_id = res_zip_region_group.id"""
        query = cr.mogrify('SELECT min(%s.id) AS id, count(DISTINCT %s.id) AS %s_count' % (self._table, self._table, group_count) + (flist and ',') + flist + ' FROM ' + from_clause + join_clause + where_clause + gb + limit_str + offset_str, where_clause_params)
        cr.execute(query)
        alldata = {}
        groupby = group_by
        for r in cr.dictfetchall():
            for fld, val in r.items():
                if val == None: r[fld] = False
            alldata[r['id']] = r
            del r['id']

        order = orderby or groupby
        data_ids = self.search(cr, uid, [('id', 'in', alldata.keys())], order=order, context=context)
        data_ids += set(alldata.keys()).difference(data_ids)

        if groupby:
            result = []
            for i in data_ids:
                group = alldata[i][groupby] or False
                if group:
                    group = zr_obj.name_get(cr, uid, [group,], context=context)[0]
                result.append({'id': i, groupby: group,})
        else:
            result = [{'id': i} for i in data_ids]

        for d in result:
            if groupby:
                d['__domain'] = [('region_group_ids', '=', alldata[d['id']][groupby] or False)] + domain
                if not isinstance(groupby_list, (str, unicode)):
                    if groupby or not context.get('group_by_no_leaf', False):
                        d['__context'] = {'group_by': groupby_list[1:]}
            if groupby and groupby in fget:
                del alldata[d['id']][groupby]
            d.update(alldata[d['id']])
            del d['id']

        if groupby and groupby in self._group_by_full:
            result = self._read_group_fill_results(cr, uid, domain, groupby, groupby_list,
                                                   aggregated_fields, result, read_group_order=order,
                                                   context=context)
        return result

    def read_group(self, cr, uid, domain, fields, groupby, offset=0, limit=None, context=None, orderby=False):
        if groupby and groupby[0] == 'region_group_id':
            res = self.read_group_region_group_ids(cr, uid, domain, fields, groupby, offset, limit, context, orderby)
        else:
            res = super(crm_lead, self).read_group(cr, uid, domain, fields, groupby, offset, limit, context, orderby)
        return res

    _columns = {
        'region_group_id': fields.dummy("Zip Region Group", type='many2one', relation="res.zip_region_group"),
        'region_group_ids': fields.function(_get_zipregion_group_ids, method=True, type='many2many', relation="res.zip_region_group", string="Zip Region Groups", readonly=True, multi='region_group_ids'),
        'region_group_names': fields.function(_get_zipregion_group_ids, method=True, type='char', string="Zip Region Groups", readonly=True, multi='region_group_ids'),
        'region_group_id_select': fields.selection(_get_zipregion_group_names, 'Zip Region Group'),
        }

crm_lead()