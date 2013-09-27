# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2013 credativ Ltd (<http://credativ.co.uk>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import time

import StringIO
import csv
from report import report_sxw
import pooler
import report
import netsvc
from tools.translate import _

class sale_report_supplier_base(object):
    def _customers_get(self, partner):
        date_from = self.context.get('date_from', None)
        date_to = self.context.get('date_to', None)
        partner_obj = pooler.get_pool(self.cr.dbname).get('res.partner')
        product_obj = pooler.get_pool(self.cr.dbname).get('product.product')
        uom_obj = pooler.get_pool(self.cr.dbname).get('product.uom')
        bom_obj = pooler.get_pool(self.cr.dbname).get('mrp.bom')
        partner_cache = {}
        product_cache = {}
        uom_cache = {}

        res = {}
        where_clauses = ["so.state NOT IN ('draft', 'cancel')", "rp.id = %s"]
        where_args = [(), (partner,)]
        if date_from:
            where_clauses.append("so.date_order >= '%s'")
            where_args.append(date_from)
        if date_to:
            where_clauses.append("so.date_order <= '%s'")
            where_args.append(date_to)
        if where_clauses:
            where_string = "WHERE " + "\n AND ".join([x[0] % x[1] for x in zip(where_clauses, where_args)])
        else:
            where_string = ""
        self.cr.execute("""WITH RECURSIVE bom_relation(bom, parent, qty) AS (
                            SELECT bom_top.id, bom_top.id, bom_top.product_qty FROM mrp_bom bom_top
                            WHERE bom_top.bom_id IS NULL
                            UNION
                            SELECT bom_child.id, bom_r.parent, bom_child.product_qty * bom_r.qty FROM mrp_bom bom_child
                            INNER JOIN bom_relation bom_r ON bom_r.bom = bom_child.bom_id
                        ), product_default_supplier AS
                        (   SELECT pp.id AS product_id,
                            (SELECT ps.name FROM product_supplierinfo ps WHERE ps.product_id = pp.id
                            ORDER BY ps.sequence ASC LIMIT 1) AS partner_id FROM product_product pp
                        ), unique_boms AS
                        (
                            SELECT tmp_bom.product_id, tmp_bom.product_uom,
                            (SELECT bom.id FROM mrp_bom bom WHERE bom.product_id = tmp_bom.product_id AND bom.product_uom = tmp_bom.product_uom AND bom_id IS NULL ORDER BY sequence ASC LIMIT 1) AS bom_id
                            FROM (SELECT product_id, product_uom FROM mrp_bom WHERE bom_id IS NULL GROUP BY product_id, product_uom) tmp_bom
                        ) SELECT rp.id, cust.id, so.date_order, pp.id, SUM(sol.product_uom_qty * COALESCE(br.qty, 1.0)), sol.product_uom
                        FROM sale_order so
                        INNER JOIN res_partner cust ON cust.id = so.partner_id
                        INNER JOIN sale_order_line sol ON sol.order_id = so.id
                        LEFT OUTER JOIN unique_boms ubom ON ubom.product_id = sol.product_id
                        LEFT OUTER JOIN bom_relation br ON br.parent = ubom.bom_id AND br.parent != br.bom
                        LEFT OUTER JOIN mrp_bom bom ON br.bom = bom.id
                        INNER JOIN product_product pp ON pp.id = COALESCE(bom.product_id, sol.product_id)
                        LEFT OUTER JOIN product_default_supplier ds ON ds.product_id = pp.id
                        LEFT OUTER JOIN res_partner rp ON ds.partner_id = rp.id
                        %s
                        GROUP BY rp.id, cust.id, so.date_order, pp.id, sol.product_uom
                        ORDER BY rp.id, cust.id, so.date_order, pp.id
                   """ % where_string)
        data = self.cr.fetchall()

        for row in data:
            partner = partner_cache.setdefault(row[1], partner_obj.browse(self.cr, self.uid, row[1], context=self.context.copy()))
            product = product_cache.setdefault(row[3], product_obj.browse(self.cr, self.uid, row[3], context=self.context.copy()))
            uom = uom_cache.setdefault(row[5], uom_obj.browse(self.cr, self.uid, row[5], context=self.context.copy()))
            res.setdefault(partner, {}).setdefault(uom, []).append((row[2], product, row[4]))

        return res

    def _adr_get(self, partner, type):
        res = []
        res_partner = pooler.get_pool(self.cr.dbname).get('res.partner')
        res_partner_address = pooler.get_pool(self.cr.dbname).get('res.partner.address')
        addresses = res_partner.address_get(self.cr, self.uid, [partner.id], [type])
        adr_id = addresses and addresses[type] or False
        result = {
                  'name': False,
                  'street': False,
                  'street2': False,
                  'city': False,
                  'zip': False,
                  'state_id':False,
                  'country_id': False,
                 }
        if adr_id:
            result = res_partner_address.read(self.cr, self.uid, [adr_id], context=self.context.copy())
            result[0]['country_id'] = result[0]['country_id'] and result[0]['country_id'][1] or False
            result[0]['state_id'] = result[0]['state_id'] and result[0]['state_id'][1] or False
            return result

        res.append(result)
        return res

    def _date_text_get(self):
        if self.context.get('date_from') and self.context.get('date_from'):
            return _('From %s to %s') % (self.context.get('date_from'), self.context.get('date_to'),)
        elif self.context.get('date_from'):
            return _('From %s') % (self.context.get('date_from'),)
        elif self.context.get('date_to'):
            return _('To %s') % (self.context.get('date_to'),)
        return ''

class sale_report_supplier(report_sxw.rml_parse, sale_report_supplier_base):
    def __init__(self, cr, uid, name, context):
        super(sale_report_supplier, self).__init__(cr, uid, name, context=context)
        self.localcontext.update( {
            'time': time,
            'adr_get': self._adr_get,
            'getCustomerData': self._customers_get,
            'getDateText': self._date_text_get,
        })
        self.context = context

report_sxw.report_sxw('report.sale.supplier.pdf', 'res.partner', 'addons/sale_report_supplier/sale_report_supplier.rml', parser=sale_report_supplier)

def encode(obj):
    if hasattr(obj, 'encode'):
        return obj.encode('utf-8')
    elif obj is False:
        return None
    else:
        return obj

class csv_report(report.interface.report_int):
    def __init__(self, name, generator):
        super(csv_report, self).__init__(name)
        self.generator = generator

    def create(self, cr, uid, ids, data, context):
        f = StringIO.StringIO()
        csv_writer = csv.writer(f)

        for row in self.generator(cr, uid, ids, data, context):
            row = [encode(cell) for cell in row]
            csv_writer.writerow(row)

        return f.getvalue(), 'csv'

def csv_register(name, generator):
    if not netsvc.Service.exists(name):
        csv_report(name, generator)

class sale_report_supplier_csv_base(sale_report_supplier_base):
    cr = None
    uid = None
    context = None

    def __init__(self, cr, uid, context):
        self.cr = cr
        self.uid = uid
        self.context = context.copy()

def sale_report_supplier_csv(cr, uid, ids, data, context):
    row = ['Supplier Ref',
           'Supplier',
           'Customer Ref',
           'Customer',
           'Date',
           'Product Code',
           'Product Name',
           'QTY',
           'UoM']
    yield row

    report_base = sale_report_supplier_csv_base(cr, uid, context)
    res_partner = pooler.get_pool(cr.dbname).get('res.partner')
    res_partner_address = pooler.get_pool(cr.dbname).get('res.partner.address')

    for supplier in res_partner.browse(cr, uid, ids, context=context):
        for customer, customerdata in report_base._customers_get(supplier.id).iteritems():
            for uom, data in customerdata.iteritems():
                for datarow in data:
                    row = [supplier.ref,            # Supplier Ref
                           supplier.name,           # Supplier
                           customer.ref,            # Customer Ref
                           customer.name,           # Customer
                           datarow[0],              # Date
                           datarow[1].default_code, # Product Code
                           datarow[1].name,         # Product Name
                           datarow[2],              # QTY
                           uom.name,                # UoM
                          ]
                    yield row

csv_register('report.sale.supplier.csv', sale_report_supplier_csv)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
