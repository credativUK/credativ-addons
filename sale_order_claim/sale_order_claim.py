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

_issue_models = {
    'sale.order.line': {'desc': 'Sale order lines',
                        'order_id_field': 'order_id'},
    'stock.move':      {'desc': 'Stock moves',
                        'order_id_field': 'order_id'},
    'stock.picking':   {'desc': 'Stock pickings',
                        'order_id_field': 'order_id'},
    }

def _issue_model_selection(obj, cr, uid, context=None):
    return [(model, im['desc']) for model, im in _issue_models.items()]


class sale_order_claim(osv.osv):
    '''
    Sale order claim. This model specialises crm.claim for making
    claims against sale orders. It assumes that the crm.claim.ref
    fields points to a sale.order resource and transfers this property
    into its own sale_order_line field.
    '''
    _inherit = 'crm.claim'
    _name = 'sale.order.claim'
    _description = 'Claim against a sale order'

    def _sum_items(self, cr, uid, sale_order_id, context=None):
        product_pool = self.pool.get('product.product')
        shipping_ids = product_pool.search(cr, uid, [('full_name', 'ilike', '%shipping%')], context=context)

        ol_pool = self.pool.get('sale.order.line')
        line_ids = ol_pool.search(cr, uid, [('order_id','=',sale_order_id),
                                            ('product_id','not in',shipping_ids)], context=context)
        return sum([ol['price_unit'] for ol in ol_pool.read(cr, uid, line_ids, ['price_unit'], context=context)])
        
    def _get_items_total(self, cr, uid, ids, field_name, arg, context=None):
        return dict([(claim.id, self._sum_items(cr, uid, claim.sale_order_id.id, context=context))
                     for claim in self.browse(cr, uid, ids, context=context)])

    def _sum_shipping(self, cr, uid, sale_order_id, context=None):
        product_pool = self.pool.get('product.product')
        shipping_ids = product_pool.search(cr, uid, [('full_name', 'ilike', '%shipping%')], context=context)

        ol_pool = self.pool.get('sale.order.line')
        shipping_ids = ol_pool.search(cr, uid, [('order_id','=',sale_order_id),
                                                ('product_id','in',shipping_ids)],
                                      context=context)
        return sum([ol['price_unit'] for ol in ol_pool.read(cr, uid, shipping_ids, ['price_unit'], context=context)])
        
    def _get_shipping_charge(self, cr, uid, ids, field_name, arg, context=None):
        return dict([(claim.id, self._sum_shipping(cr, uid, claim.sale_order_id.id, context=context))
                     for claim in self.browse(cr, uid, ids, context=context)])

    def _sum_discounts(self, cr, uid, sale_order_id, context=None):
        ol_pool = self.pool.get('sale.order.line')
        line_ids = ol_pool.search(cr, uid, [('order_id','=',sale_order_id)], context=context)
        return -sum([ol['price_unit'] * (ol['discount'] / 100.0)
                     for ol in ol_pool.read(cr, uid, line_ids, ['price_unit', 'discount'], context=context)])
        
    def _get_order_discount(self, cr, uid, ids, field_name, arg, context=None):
        return dict([(claim.id, self._sum_discounts(cr, uid, claim.sale_order_id.id, context=context))
                     for claim in self.browse(cr, uid, ids, context=context)])

    def default_get(self, cr, uid, fields, context=None):
        rec_id = context and context.get('active_id', False)
        if rec_id:
            return {'active': True,
                    'sale_order_id': rec_id,
                    'order_issue_ids': self.reread_issues(cr, uid, ids=[], sale_order_id=rec_id, order_issue_ids=[], context=context)['value']['order_issue_ids']}
        else:
            return super(sale_order_claim, self).default_get(cr, uid, fields, context=context)

    def _update_issues(self, cr, uid, claim, claim_id, context=None):
        '''
        Given a dict representing a draft claim (from create or
        write's vals argument), returns an updated order_issue_ids
        value with the correct order_claim_id.
        '''
        if isinstance(claim_id, (tuple, list)):
            claim_id = claim_id[0]
        new_issue_lines = []
        for issue_line in claim['order_issue_ids']:
            if isinstance(issue_line, (list, tuple)):
                op, id, rec = issue_line
            else:
                continue
            if op in [0,1]:
                rec['order_claim_id'] = claim_id
                # FIXME Sometimes you've made the issues list just a
                # list of dicts and ignored the other values
                new_issue_lines.append((op, id, rec))

        return new_issue_lines

    def create(self, cr, uid, vals, context=None):
        '''
        When creating a new sale.order.claim, set any existing
        sale.order.issue reccords' order_claim_id fields to the new
        claim's ID.
        '''
        res_id = super(sale_order_claim, self).create(cr, uid, vals, context=context)
        vals['order_issue_ids'] = self._update_issues(cr, uid, vals, res_id, context=context)
        self.write(cr, uid, res_id, vals, context=context)
        return res_id

    def write(self, cr, uid, ids, vals, context=None):
        if 'sale_order_id' in vals and 'ref' not in vals:
            vals['ref'] = 'sale.order,%d' % vals['sale_order_id']
        if isinstance(ids, (int, long)) or len(ids) == 1 and 'order_issue_ids' in vals:
            # We only need to update the issues if some new issues
            # have been supplied
            vals['order_issue_ids'] = self._update_issues(cr, uid, vals, ids, context=context)
        return super(sale_order_claim, self).write(cr, uid, ids, vals, context=context)

    _columns = {
        'sale_order_id': fields.many2one(
            'sale.order',
            'Sale order',
            domain=[('state','not in',('draft','cancel'))],
            required=True),
        'issue_model': fields.selection(
            selection=_issue_model_selection,
            string='Issue type',
            required=True),
        'whole_order_claim': fields.boolean(
            'Claim against whole order',
            required=True),
        'state': fields.selection(
            selection=(('draft', 'Draft'),
                       ('opened', 'Opened'),
                       ('processed', 'Processed'),
                       ('rejected', 'Rejected'),
                       ('cancelled', 'Cancel')),
            required=True,
            string='State'),
        'shop_id': fields.related(
            'sale_order_id', 'shop_id',
            type='many2one',
            relation='sale.shop',
            readonly=True,
            string='Shop'),
        'origin': fields.related(
            'sale_order_id',
            'origin',
            type='char',
            readonly=True,
            string='Source document'),
        'client_order_ref': fields.related(
            'sale_order_id',
            'client_order_ref',
            type='char',
            readonly=True,
            string='Customer ref.'),
        'order_state': fields.related(
            'sale_order_id',
            'state',
            type='char',
            readonly=True,
            string='Order state'),
        'date_order': fields.related(
            'sale_order_id',
            'date_order',
            type='date',
            string='Order date',
            readonly=True),
        'merchandiser_id': fields.related(
            'sale_order_id', 'user_id',
            type='many2one',
            relation='res.users',
            readonly=True,
            string='Merchandiser'),
        'customer_id': fields.related(
            'sale_order_id', 'partner_id',
            type='many2one',
            relation='res.partner',
            readonly=True,
            string='Customer'),
        'partner_shipping_id': fields.related(
            'sale_order_id', 'partner_shipping_id',
            type='many2one',
            relation='res.partner.address',
            readonly=True,
            string='Customer shipping addr.'),
        'shipped': fields.related(
            'sale_order_id',
            'shipped',
            type='boolean',
            readonly=True,
            string='Shipped?'),
        'invoiced': fields.related(
            'sale_order_id',
            'invoiced',
            type='boolean',
            readonly=True,
            string='Invoiced?'),
        'order_items_total': fields.function(
            _get_items_total,
            type='float',
            readonly=True,
            string='Items total'),
        'shipping_charge': fields.function(
            _get_shipping_charge,
            type='float',
            readonly=True,
            string='Shipping charge'),
        'order_discount': fields.function(
            _get_order_discount,
            type='float',
            readonly=True,
            string='Discount'),
        'order_total': fields.related(
            'sale_order_id',
            'amount_total',
            type='float',
            readonly=True,
            string='Order total'),
        'order_issue_ids': fields.one2many(
            'sale.order.issue',
            'order_claim_id',
            string='Claim issues',
            oldname='claim_line_ids'),
        }

    _defaults = {
        'name': lambda self, cr, uid, ctx: self.pool.get('ir.sequence').next_by_code(cr, uid, 'sale.order.claim'),
        'state': 'draft',
        'active': True,
        'whole_order_claim': False,
        'issue_model': 'sale.order.line',
        }

    def onchange_sale_order(self, cr, uid, ids, sale_order_id, order_issue_ids, context=None):
        res = self.reread_issues(cr, uid, ids, sale_order_id, order_issue_ids, context=None)

        so_pool = self.pool.get('sale.order')
        sale_order = so_pool.browse(cr, uid, sale_order_id, context=context)
        if sale_order:
            # I don't like this. Why do I have to repeat all these
            # relations?
            res['value'].update({
                    'shop_id': sale_order.shop_id.name,
                    'origin': sale_order.origin,
                    'client_order_ref': sale_order.client_order_ref,
                    'order_state': sale_order.state,
                    'date_order': sale_order.date_order,
                    'merchandiser_id': sale_order.user_id.name,
                    'customer_id': sale_order.partner_id.name,
                    'partner_shipping_id': sale_order.partner_shipping_id.name,
                    'shipped': sale_order.shipped,
                    'invoiced': sale_order.invoiced,
                    'order_items_total': self._sum_items(cr, uid, sale_order_id, context=context),
                    'shipping_charge': self._sum_shipping(cr, uid, sale_order_id, context=context),
                    'order_discount': self._sum_discounts(cr, uid, sale_order_id, context=context),
                    'order_total': sale_order.amount_total})

        return res

    def reread_issues(self, cr, uid, ids, sale_order_id, order_issue_ids, context=None):
        '''
        This method is called when the sale_order_id is changed. It
        causes the list of issues to be re-read. This is necessary
        because order_issue_ids is not a related field to
        sale_order_id.
        '''
        if context is None:
            context = {}

        issue_pool = self.pool.get('sale.order.issue')
        #claim = self.browse(cr, uid, ids, context=context)
        context['sale_order_id'] = sale_order_id
        # FIXME Which sale_order_id and which order_issue_ids
        # should we use? New ones or current ones?
        return {'value': {'order_issue_ids': issue_pool.read(cr, uid, [], ['id'], context=context),
                          'sale_order_id': sale_order_id}}

    def onchange_issue_model(self, cr, uid, ids, new_issue_model, context=None):
        # set _visible fields for each possible model type
        visibles = dict([('order_issue_ids.%s_visible' % (model.replace('.','_'),), model == new_issue_model)
                         for model in _issue_models.keys()])

        # Don't allow changing the model if issues already exist
        if isinstance(ids, int) or (isinstance(ids, (list, tuple)) and len(ids) == 1):
            claim = self.browse(cr, uid, ids, context=context)
            if claim.order_issue_ids:
                return {'value': {'issue_model': claim.issue_model},
                        'warning': {'title': 'Change not allowed',
                                    'message': 'The issue model may not be changed while issues exist. '
                                    'You may remove all the issues and then change the issue model.'}}
            else:
                new_issues = self.reread_issues(cr, uid, ids, claim.sale_order_id, claim.order_issue_ids, context=context)['value']['order_issue_ids']
                visibles.update({'order_issue_ids': new_issues})
                return {'value': visibles}

        visibles.update({'issue_model': new_issue_model})
        return {'value': visibles}

    def toggle_whole_order_claim(self, cr, uid, ids, whole_order_claim, context=None):
        if whole_order_claim:
            for claim in self.browse(cr, uid, ids, context=context):
                item_pool = self.pool.get(claim.issue_model)
                # TODO Mark as selected

        else:
            # We can't really remove all the items from the claim
            pass

    def save_draft(self, cr, uid, ids, context=None):
        '''
        This method is necessary when the form is presented in a
        pop-up window.
        '''
        return {'view_mode': 'tree,form',
                'type': 'ir.actions.act_window_close'}

    def action_open(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'opened'}, context=context)
        return True

    def action_process(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'procesed'}, context=context)
        return True

    def action_reject(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'rejected'}, context=context)
        return True

    def action_cancel(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'cancelled'}, context=context)
        return True

sale_order_claim()


class sale_order_issue(osv.osv):
    '''
    Sale order issue. This model specialises crm.claim.line for
    logging issues against specific parts of a sale order. It parses
    its field resource as a resource of: sale.order.line, stock.move,
    or stock.picking, storing a reference in the respective _id field.
    '''
    _inherit = 'crm.claim.line'
    _name = 'sale.order.issue'
    _description = 'Individual issue in a sale order claim'

    def _get_related(self, cr, uid, ids, context=None):
        '''This method parses the .resource field into (model, res_id)
        pairs, returning a dict with one pair for each resource in
        ids.'''
        return dict([(line.id, (line.resource[:line.resource.find(',')], int(line.resource[line.resource.find(',') + 1:])))
                     for line in self.browse(cr, uid, ids, context=context)])

    def _find_records_for_order(self, cr, uid, order_id, context=None):
        '''
        Implementations of this method should return a browse object
        containing all the records of the claim's issue_model which
        are related to the given order_id.
        '''
        raise NotImplementedError()

    def _make_issue_dict(self, cr, uid, issue_id, sale_order_id, claim_id, rec_id, context=None):
        '''
        Implementations of this method should return a dict containing
        all the fields needed to create a new record of their own
        issue type.
        '''
        raise NotImplementedError()

    def _issue_eq_res(self, cr, uid, issue, res, context=None):
        '''
        Implements of this method should return True if the given
        issue and the given resource represent the same thing, or
        False otherwise.

        @param issue (dict): an existing sale.order.issue
        @param res (browse_object): an existing record of the
        issue_model model
        '''
        raise NotImplementedError()

    def read(self, cr, uid, ids, fields=None, context=None, load='_classic_read'):
        '''
        Override read to include any resources from the related model
        which do not already have a related sale.order.issue. The
        purpose of this is so that the one2many list of
        sale.order.issues will always show *all* the
        sale.order.claim.issue_model resources for the appropriate
        sale.order allowing the user to tick the
        sale.order.issue.select field for them.
        '''
        # ensure order_claim_id is in the fields list
        if fields is not None and 'order_claim_id' not in fields:
            fields.append('order_claim_id')

        # read the resources using super read
        res = super(sale_order_issue, self).read(cr, uid, ids, fields=fields, context=context, load=load)
        # clean up the many2one field values produced by .read
        def clean(r):
            for k, v in r.items():
                if isinstance(v, tuple):
                    r[k] = v[0]
            return r
        res = map(clean, res)

        # find the distinct claims in the specified issues
        claim_ids = list(set([issue['order_claim_id'] for issue in res]))

        if len(claim_ids) > 1 and 'sale_order_id' not in context:
            # if the specified issues cover multiple claims and no
            # sale order has been specified, we can't add issue_model
            # resources; so we give up
            return res

        # if the specified issues are all from the same claim then add
        # any missing resources from the issue_model to the read list
        if len(claim_ids) == 1:
            claim = self.pool.get('sale.order.claim').browse(cr, uid, claim_ids[0], context=context)
            claim_id = claim.id
            sale_order_id = claim.sale_order_id.id
        elif len(claim_ids) == 0 and 'sale_order_id' in context:
            claim_id = context.get('active_model') == 'sale.order.claim' and context.get('active_id', False) or False
            sale_order_id = context['sale_order_id']
        else:
            return res

        for rec in self._find_records_for_order(cr, uid, sale_order_id, context=context):
            if not filter(lambda issue: self._issue_eq_res(cr, uid, issue, rec, context=context), res):
                res.append(self._make_issue_dict(cr, uid, False, sale_order_id, claim_id, rec, context=context))

        return res

    # def write(self, cr, uid, ids, vals, context=None):
    #     '''
    #     If a record is written with selected=False, that means the
    #     issue should be removed.
    #     '''
    #     import pdb; pdb.set_trace()
    #     res = super(sale_order_issue, self).write(cr, uid, ids, vals, context=context)
    #     if not res:
    #         return False

    #     if 'selected' in vals and vals['selected'] is False:
    #         self.unlink(cr, uid, ids, context=context)
    #         return True
    #     else:
    #         return False

    _columns = {
        'resource': fields.reference(
            'Item',
            selection=_issue_model_selection,
            size=128),
        'order_claim_id': fields.many2one(
            'sale.order.claim',
            string='Claim',
            required=True,
            oldname='claim_id'),
        'select': fields.boolean(
            'Select',
            required=True,
            help='Add this item to the claim')
        }

    _defaults = {
        'order_claim_id': lambda s, c, u, i, ctx: ctx.get('order_claim_id', None),
        'select': False,
        }

    def onchange_resource(self, cr, uid, ids, new_resource, context=None):
        if isinstance(ids, int) or (isinstance(ids, (list, tuple)) and len(ids) == 1):
            issue = self.browse(cr, uid, ids, context=context)
            model = issue.resource[:issue.resource.find(',')]
            if model != issue.order_claim_id.issue_model:
                return {'value': {'resource': False},
                        'warning': {'title': 'Wrong model',
                                    'message': 'Each issue must be against an item of the model: "%s"' %\
                                        (issue.claim_id.issue_model,)}}

    def toggle_item_selected(self, cr, uid, ids, select, order_claim_id, sale_order_id, context=None):
        pass

    def resolution_next(self, cr, uid, ids, context=None):
        resolution_pool = self.pool.get('crm.claim.resolution')
        resolution_pool.action_next(cr, uid,
                                    [claim.resolution_id.id for claim in self.browse(cr, uid, ids, context=context) if claim.resolution_id],
                                    context=context)

    def resolution_previous(self, cr, uid, ids, context=None):
        resolution_pool = self.pool.get('crm.claim.resolution')
        resolution_pool.action_previous(cr, uid,
                                        [claim.resolution_id.id for claim in self.browse(cr, uid, ids, context=context) if claim.resolution_id],
                                        context=context)

sale_order_issue()


class sale_order(osv.osv):
    '''
    Add a list of sale.order.claims to the sale.order model.
    '''
    _inherit = 'sale.order'

    _columns = {
        'claim_ids': fields.one2many(
            'sale.order.claim',
            'sale_order_id',
            string='Claims')
        }

sale_order()
