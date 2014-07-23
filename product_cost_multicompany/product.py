# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution   
#    Copyright (C) 2014 credativ ltd (<http://www.credativ.co.uk>). All Rights Reserved
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

import logging
from osv import osv, fields
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp

_logger = logging.getLogger(__name__)

class ProductProduct(osv.Model):
    _inherit = 'product.product'

    def _get_standard_price(self, cr, uid, ids, name, arg, context=None):
        context = context or {}
        price_obj = self.pool.get('product.price.multi')
        res = dict.fromkeys(ids, 0.0)
        company_id = context.get('company_id')
        if not company_id:
            context = context.copy()
            company_id = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id.id
            context['company_id'] = company_id
            _logger.warning("Product standard price read without company_id set in context. Using user company %s." % (company_id,))
        for id in ids:
            price_ids = price_obj.search(cr, uid, [('product_id', '=', id), ('company_id', '=', company_id)], context=context)
            if len(price_ids) == 1:
                res[id] = price_obj.read(cr, uid, price_ids[0], ['standard_price'], context=context)['standard_price']
            elif len(price_ids) == 0:
                res[id] = 0.0
            else:
                raise osv.except_osv("Integrity Error!", "Multiple cost prices exist for the same company for the same product")
        return res
        

    def _set_standard_price(self, cr, uid, ids, name, value, arg, context=None):
        context = context or {}
        price_obj = self.pool.get('product.price.multi')
        company_id = context.get('company_id')
        if not company_id:
            raise osv.except_osv("Error!", "Company must be set in context to write to the standard price field")
        if type(ids) not in (list, tuple):
            ids = [ids,]
        for id in ids:
            price_ids = price_obj.search(cr, uid, [('product_id', '=', id), ('company_id', '=', company_id)], context=context)
            if len(price_ids) == 1:
                price_obj.write(cr, uid, price_ids, {'standard_price': value}, context=context)
            elif len(price_ids) == 0:
                rec = {'product_id': id,
                       'company_id': company_id,
                       'standard_price': value,}
                price_obj.create(cr, uid, rec, context=context)
            else:
                raise osv.except_osv("Integrity Error!", "Multiple cost prices exist for the same company for the same product")
        return True

    _columns = {
        'standard_price': fields.function(_get_standard_price, fnct_inv=_set_standard_price, string='Cost', digits_compute=dp.get_precision('Purchase Price'), help="Cost price of the product used for standard stock valuation in accounting and used as a base price on purchase orders.", groups="base.group_user"),
        'standard_price_multi': fields.one2many('product.price.multi', 'product_id', string='Multi Company Standard Prices')
    }

    def create(self, cr, uid, vals, context=None):
        # Get the company from the user for create to avoid exception when writing to standard_price
        context = context or {}
        ctx = context.copy()
        company_id = self.pool.get('res.users').browse(cr, uid, uid).company_id.id
        ctx['company_id'] = company_id
        for a in range(0, len(vals.get('standard_price_multi', []))):
            if vals['standard_price_multi'][a][2]['company_id'] == company_id:
                vals['standard_price'] = vals['standard_price_multi'][a][2].get('standard_price', vals.get('standard_price', 0.0))
                del vals['standard_price_multi'][a]
                break
        return super(ProductProduct, self).create(cr, uid, vals, context=ctx)

    def onchange_cost_method(self, cr, uid, ids, cost_method, standard_price_multi):
        # If we are becoming 'standard' we just change
        multi_obj = self.pool.get('product.price.multi')
        lines = []
        for line in standard_price_multi:
            if cost_method == 'average':
                if line[0] == 0:
                    line[2].update({'standard_price': 0.0, 'cost_method': 'average'})
                elif line[0] == 1:
                    line_rec = multi_obj.browse(cr, uid, line[1])
                    line[2].update({'standard_price': line_rec.standard_price, 'cost_method': 'average'})
                elif line[0] in (2, 3, 4):
                    line[0] = 1
                    line[2] = {'cost_method': 'average'}
                else:
                    raise NotImplementedError("Cannot handle m2o record %s" % (line,))
            else:
                if line[0] in (0, 1):
                    line[2].update({'cost_method': 'standard'})
                elif line[0] in (2, 3, 4):
                    line[0] = 1
                    line[2] = {'cost_method': 'standard'}
                else:
                    raise NotImplementedError("Cannot handle m2o record %s" % (line,))
            lines.append(line)

        if lines:
            return {'value': {'standard_price_multi': lines}}
        else:
            return {}

    def do_change_standard_price(self, cr, uid, ids, datas, context=None):
        """ Changes the Standard Price of Product and creates an account move accordingly.
        @param datas : dict. contain default datas like new_price, stock_output_account, stock_input_account, stock_journal
        @param context: A standard dictionary
        @return:

        Overridden completly so that the qty_available is only taken from the current company warehouse
        """
        context = context or {}
        company_id = context.get('company_id')
        if not company_id:
            raise osv.except_osv("Error!", "Company must be set in context to write to the standard price field")

        location_obj = self.pool.get('stock.location')
        move_obj = self.pool.get('account.move')
        move_line_obj = self.pool.get('account.move.line')

        new_price = datas.get('new_price', 0.0)
        stock_output_acc = datas.get('stock_output_account', False)
        stock_input_acc = datas.get('stock_input_account', False)
        journal_id = datas.get('stock_journal', False)
        move_ids = []
        loc_ids = location_obj.search(cr, uid,[('usage','=','internal'), ('company_id', '=', company_id)])
        ctx = {'company_id': company_id, 'location': loc_ids, 'force_company': company_id}
        for product in self.browse(cr, uid, ids, context=ctx):
            if product.valuation != 'real_time':
                continue
            account_valuation = product.categ_id.property_stock_valuation_account_id
            account_valuation_id = account_valuation and account_valuation.id or False
            if not account_valuation_id: raise osv.except_osv(_('Error!'), _('Specify valuation Account for Product Category: %s.') % (product.categ_id.name))
            qty = product.qty_available
            diff = product.standard_price - new_price
            if not diff: raise osv.except_osv(_('Error!'), _("No difference between standard price and new price!"))
            if qty:
                if not journal_id:
                    journal_id = product.categ_id.property_stock_journal and product.categ_id.property_stock_journal.id or False
                if not journal_id:
                    raise osv.except_osv(_('Error!'),
                        _('Please define journal '\
                            'on the product category: "%s" (id: %d).') % \
                            (product.categ_id.name,
                                product.categ_id.id,))
                move_id = move_obj.create(cr, uid, {
                            'journal_id': journal_id,
                            'company_id': company_id
                            }, context=ctx)

                move_ids.append(move_id)

                if diff > 0:
                    if not stock_input_acc:
                        stock_input_acc = product.\
                            property_stock_account_input.id
                    if not stock_input_acc:
                        stock_input_acc = product.categ_id.\
                                property_stock_account_input_categ.id
                    if not stock_input_acc:
                        raise osv.except_osv(_('Error!'),
                                _('Please define stock input account ' \
                                        'for this product: "%s" (id: %d).') % \
                                        (product.name,
                                            product.id,))
                    amount_diff = qty * diff
                    move_line_obj.create(cr, uid, {
                                'name': product.name,
                                'account_id': stock_input_acc,
                                'debit': amount_diff,
                                'move_id': move_id,
                                'product_id': product.id,
                                }, context=ctx)
                    move_line_obj.create(cr, uid, {
                                'name': product.categ_id.name,
                                'account_id': account_valuation_id,
                                'credit': amount_diff,
                                'move_id': move_id,
                                'product_id': product.id,
                                }, context=ctx)
                elif diff < 0:
                    if not stock_output_acc:
                        stock_output_acc = product.\
                            property_stock_account_output.id
                    if not stock_output_acc:
                        stock_output_acc = product.categ_id.\
                                property_stock_account_output_categ.id
                    if not stock_output_acc:
                        raise osv.except_osv(_('Error!'),
                                _('Please define stock output account ' \
                                        'for this product: "%s" (id: %d).') % \
                                        (product.name,
                                            product.id,))
                    amount_diff = qty * -diff
                    move_line_obj.create(cr, uid, {
                                    'name': product.name,
                                    'account_id': stock_output_acc,
                                    'credit': amount_diff,
                                    'move_id': move_id,
                                    'product_id': product.id,
                                }, context=ctx)
                    move_line_obj.create(cr, uid, {
                                    'name': product.categ_id.name,
                                    'account_id': account_valuation_id,
                                    'debit': amount_diff,
                                    'move_id': move_id,
                                    'product_id': product.id,
                                }, context=ctx)
        self.write(cr, uid, ids, {'standard_price': new_price}, context=context)

        return move_ids

class ProductPriceMulti(osv.Model):
    _name = 'product.price.multi'
    _description = 'Cost Multi Company'
    _rec_name = 'company_id'
    _order = 'product_id asc, company_id asc'

    _columns = {
        "product_id" : fields.many2one('product.product', string='Product', required=True, ondelete='cascade'),
        "company_id" : fields.many2one('res.company', string='Company', required=True),
        "currency_id" : fields.related('company_id', 'currency_id', type='many2one', relation='res.currency', string='Company Currency', readonly=True),
        "cost_method" : fields.related('product_id', 'cost_method', type='selection',
                                       selection=[('standard','Standard Price'), ('average','Average Price')], string='Costing Method', readonly=True,
                                       help="Standard Price: The cost price is manually updated at the end of a specific period (usually every year). \nAverage Price: The cost price is recomputed at each incoming shipment."),
        'standard_price': fields.float('Cost', digits_compute=dp.get_precision('Purchase Price'), help="Cost price of the product used for standard stock valuation in accounting and used as a base price on purchase orders. In company currency."),
    }

    _sql_constraints = [
        ('product_price_multi_unique', 'unique (product_id,company_id)', 'Products can only have one cost price per company!')
    ]

    def write(self, cr, uid, ids, values, context=None):
        if 'company_id' in values:
            for price in self.browse(cr, uid, ids, context=context):
                if price.company_id != values['company_id'] and price.cost_method == 'average':
                    raise osv.except_osv("Error!", "It is not possible to change the Company for a price line when Average Price is used.")
        return super(ProductPriceMulti, self).write(cr, uid, ids, values, context=context)

    def unlink(self, cr, uid, ids, context=None):
        for price in self.browse(cr, uid, ids, context=context):
            if price.cost_method == 'average':
                raise osv.except_osv("Error!", "It is not possible to delete a price line when Average Price is used.")
        return super(ProductPriceMulti, self).unlink(cr, uid, ids, context=context)

    def action_update_price(self, cr, uid, ids, context=None):
        assert len(ids) == 1, 'This option should only be used for a single id at a time.'
        context = context or {}
        ir_model_data = self.pool.get('ir.model.data')

        try:
            form_id = ir_model_data.get_object_reference(cr, uid, 'stock', 'view_change_standard_price')[1]
        except ValueError:
            form_id = False
        ctx = context.copy()
        price_line = self.browse(cr, uid, ids[0], context=context)
        ctx.update({
                'active_id': price_line.product_id.id,
                'active_ids': [price_line.product_id.id,],
                'company_id': price_line.company_id.id,
            })
        return {
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'stock.change.standard.price',
                'target': 'new',
                'context': ctx,
                'name': 'Change Multi Company Standard Price',
                'views': [(form_id, 'form')],
                'view_id': form_id,
            }

class ChangeStandardPrice(osv.TransientModel):
    _inherit = "stock.change.standard.price"

    def default_get(self, cr, uid, fields, context=None):
        if context is None:
            context = {}

        res = super(ChangeStandardPrice, self).default_get(cr, uid, fields, context=context)

        product_pool = self.pool.get('product.product')
        product_obj = product_pool.browse(cr, uid, context.get('active_id', False), context=context)

        ctx = context.copy()
        if ctx.get('company_id'):
            ctx['force_company'] = ctx.get('company_id')
        accounts = product_pool.get_product_accounts(cr, uid, context.get('active_id', False), context=ctx)

        price = product_obj.standard_price

        if 'new_price' in fields:
            res.update({'new_price': price})
        if 'stock_account_input' in fields:
            res.update({'stock_account_input': accounts['stock_account_input']})
        if 'stock_account_output' in fields:
            res.update({'stock_account_output': accounts['stock_account_output']})
        if 'stock_journal' in fields:
            res.update({'stock_journal': accounts['stock_journal']})
        if 'enable_stock_in_out_acc' in fields:
            res.update({'enable_stock_in_out_acc': True})

        return res

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
