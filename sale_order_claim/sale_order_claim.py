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

    def write(self, cr, uid, ids, vals, context=None):
        if 'sale_order_id' in vals and 'ref' not in vals:
            vals['ref'] = 'sale.order,%d' % vals['sale_order_id']
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
        # 'order_id_field': fields.char(
        #     'Issue model order link field',
        #     size=64,
        #     required=True,
        #     help='''Field name of the field on the issue model that points to a sale order.'''),
        'whole_order_claim': fields.boolean(
            'Claim against whole order',
            required=True),
        'state': fields.selection(
            selection=(('draft', 'Draft'),
                       ('opened', 'Open'),
                       ('processing', 'Process'),
                       ('review', 'Review'),
                       ('approved', 'Approve'),
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
        'whole_order_claim': False,
        'issue_model': 'sale.order.line',
        #'order_id_field': 'order_id',
        }

    def onchange_issue_model(self, cr, uid, ids, new_issue_model, context=None):
        # Don't allow changing the model if issues already exist
        if isinstance(ids, int) or (isinstance(ids, (list, tuple)) and len(ids) == 1):
            claim = self.browse(cr, uid, ids, context=context)
            if claim.order_issue_ids:
                return {'value': {'issue_model': claim.issue_model},
                        'warning': {'title': 'Change not allowed',
                                    'message': 'The issue model may not be changed while issues exist. '
                                    'You may remove all the issues and then change the issue model.'}}
            #else:
            #    return {'value': {'issue_model': new_issue_model}}

        return {'issue_model': new_issue_model}

    def toggle_whole_order_claim(self, cr, uid, ids, whole_order_claim, context=None):
        if whole_order_claim:
            for claim in self.browse(cr, uid, ids, context=context):
                item_pool = self.pool.get(claim.issue_model)

        else:
            # We can't really remove all the items from the claim
            pass


    def action_open(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'opened'}, context=context)
        return True

    def action_process(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'processing'}, context=context)
        return True

    def action_review(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'review'}, context=context)
        return True

    def action_approve(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'approved'}, context=context)
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

    def _make_issue_dict(self, cr, uid, claim_id, rec_id, fields=None, context=None):
        '''
        Implementations of this method should return a dict containing
        all the fields needed to create a new record of their own
        issue type.
        '''
        raise NotImplementedError()

    def read(self, cr, uid, ids, fields=None, context=None):
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

        # read the resources using super.read
        res = super(sale_order_issue).read(cr, uid, ids, fields=fields, context=context)

        # find the distinct claims in the specified issues
        claim_ids = set([issue['order_claim_id'] for (id, issue) in res.items()])

        if len(claim_ids) == 1:
            # if the specified issues are all from the same claim then
            # add any missing resources from the issue_model to the
            # read list
            claim = self.pool.get('sale.order.claim').browse(cr, uid, claim_ids[0], context=context)

            for rec in self._find_records_for_order(cr, uid, claim.sale_order_id, context=context):
                if res.id not in res:
                    res[rec.id] = self._make_issue_dict(cr, uid, claim.id, rec.id, fields=fields, context=context)

        return res

    def write(self, cr, uid, ids, vals, context=None):
        '''
        If a record is written with selected=False, that means the
        issue should be removed.
        '''
        if 'selected' in vals and vals['selected'] is False:
            self.unlink(cr, uid, ids, context=context)

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
        'select': False,
        }

    # def _ensure_claim_is_sale_order_claim(self, cr, uid, ids, context=None):
    #     return all([line.claim_id.ref[:line.claim_id.ref.find(',')] == 'sale.order'
    #                 for line in self.browse(cr, uid, ids, context=context)])

    # _constraints = [
    #     (_ensure_claim_is_sale_order_claim,
    #      'Parent claim of an order issue must be a claim against a sale order.',
    #      ['claim_id']),
    #     ]

    def onchange_resource(self, cr, uid, ids, new_resource, context=None):
        if isinstance(ids, int) or (isinstance(ids, (list, tuple)) and len(ids) == 1):
            issue = self.browse(cr, uid, ids, context=context)
            model = issue.resource[:issue.resource.find(',')]
            if model != issue.claim_id.issue_model:
                return {'value': {'resource': False},
                        'warning': {'title': 'Wrong model',
                                    'message': 'Each issue must be against an item of the model: "%s"' %\
                                        (issue.claim_id.issue_model,)}}

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
