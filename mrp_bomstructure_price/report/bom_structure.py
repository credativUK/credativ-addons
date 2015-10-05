# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
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

from openerp import _, models
from openerp.exceptions import ValidationError
from openerp.report import report_sxw
from openerp.addons.product import _common


class bom_structure(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(bom_structure, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'get_children': self.get_children,
        })

    def _bom_explode(self, bom, product, factor, properties=None, level=0,
                     previous_products=None, master_bom=None):
        """
        Finds Products and Work Centers for related BoM for manufacturing
        order.

        @param bom: BoM of particular product template.
        @param product: Select a particular variant of the BoM. If False use
                        BoM without variants.
        @param factor: Factor represents the quantity, but in UoM of the BoM,
                       taking into account the numbers produced by the BoM
        @param properties: A List of properties Ids.
        @param level: Depth level to find BoM lines starts from 0.
        @param previous_products: List of product previously used by bom
                                  explode to avoid recursion
        @param master_bom: When recursing, used to display the name of the
                           master bom
        @return: Tuple of final cost price and a list of dictionaries
                 containing product details.
        """
        bom_obj = bom.env["mrp.bom"]
        uom_obj = bom.env["product.uom"]
        master_bom = master_bom or bom

        def _factor(factor, product_efficiency, product_rounding):
            factor = factor / (product_efficiency or 1.0)
            factor = _common.ceiling(factor, product_rounding)
            if factor < product_rounding:
                factor = product_rounding
            return factor

        factor = _factor(factor, bom.product_efficiency, bom.product_rounding)

        total = 0
        result = []

        for bom_line in bom.bom_line_ids:
            if bom_obj._skip_bom_line(bom_line, product):
                continue
            if set(map(int, bom_line.property_ids or [])) - set(properties or []):
                continue

            if previous_products and bom_line.product_id.product_tmpl_id.id in previous_products:
                raise ValidationError(_('BoM "%s" contains a BoM line with a product recursion: "%s".') % (master_bom.name, bom_line.product_id.name_get()[0][1]))

            quantity = _factor(bom_line.product_qty * factor, bom_line.product_efficiency, bom_line.product_rounding)
            bom_id = bom_obj._bom_find(product_id=bom_line.product_id.id, properties=properties)

            # If BoM should not behave like Phantom, just add the product,
            # otherwise explode further
            if bom_line.type != "phantom" and (not bom_id or bom_obj.browse(bom_id).type != "phantom"):
                price = bom_line.product_id.standard_price * bom_line.product_uom._compute_qty(bom_line.product_uom.id, quantity, bom_line.product_id.uom_id.id)
                total += price
                result.append({
                    'bom_line': bom_line,
                    'product_qty': quantity,
                    'subtotal': price,
                    'level': level + 1 if level < 6 else 6,
                })
            elif bom_id:
                all_prod = [bom.product_tmpl_id.id] + (previous_products or [])
                bom2 = bom_obj.browse(bom_id)

                # We need to convert to units/UoM of chosen BoM
                factor2 = uom_obj._compute_qty(bom_line.product_uom.id,
                                               quantity, bom2.product_uom.id)
                quantity2 = factor2 / bom2.product_qty

                res = self._bom_explode(bom2, bom_line.product_id, quantity2,
                                        properties=properties, level=level + 1,
                                        previous_products=all_prod,
                                        master_bom=master_bom)

                total += res[0]['subtotal']
                res[0].update(bom_line=bom_line)
                result.extend(res)
            else:
                raise ValidationError(_('BoM "%s" contains a phantom BoM line but the product "%s" does not have any BoM defined.') % (bom.name, bom_line.product_id.name_get()[0][1]))
        data = {
            'product_qty': factor,
            'subtotal': total,
            'level': level if level < 6 else 6,
            'bom': bom,
        }

        # we are building a pre-order trace
        result.insert(0, data)

        return result

    def get_children(self, bom):
        bom.ensure_one()
        return self._bom_explode(bom, None, bom.product_qty)


class report_mrpbomstructure(models.AbstractModel):
    _name = 'report.mrp_bomstructure_price.report_mrpbomstructure'
    _inherit = 'report.abstract_report'
    _template = 'mrp_bomstructure_price.report_mrpbomstructure'
    _wrapped_report_class = bom_structure
