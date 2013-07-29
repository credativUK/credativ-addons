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

from osv import fields, osv
from crm import crm

class crm_claim(osv.osv):
    '''
    We extend crm.claim to include claim lines, allowing a single
    claim to cover multiple items. crm.claim will still reference a
    single resource through its ref field, the lines will be in
    addition to this. For example, a claim may reference a single sale
    order, and some selection of lines from that sale order.
    '''
    _inherit = 'crm.claim'
    _name = 'crm.claim'

    _columns = {
        'create_uid': fields.many2one(
            'res.users',
            'Creator',
            readonly=True),
        'write_uid': fields.many2one(
            'res.users',
            'Last Modification User',
            readonly=True),
        'claim_line_ids': fields.one2many(
            'crm.claim.line',
            'claim_id',
            string='Claim items'),
        'category': fields.many2one(
            'crm.claim.line.category',
            string='Category'),
        'reason': fields.many2one(
            'crm.claim.line.category',
            string='Reason'),
        'resolution_id': fields.many2one(
            'crm.claim.resolution',
            string='Resolution')
        }

    def claim_lines_from_all(self, cr, uid, ids, res_ids, context=None):
        '''
        This method creates claim lines for all the given res_ids
        (which should be resources of an appropriate model).
        '''
        pass

crm_claim()

class crm_claim_category(osv.osv):
    '''
    CRM claim category. Users should create an (optionally
    hierarchical) list of categories describing different kinds of
    claims that can be made. Resources of this model may be parents of
    resources of the crm.claim.line.category model.
    '''
    _name = 'crm.claim.category'
    _description = 'Categories of CRM claims'
    _order = 'parent_categ_id,sequence'

    _columns = {
        'name': fields.char(
            'Category',
            required=True,
            size=64),
        'sequence': fields.integer(
            'Sequence'),
        'parent_categ_id': fields.many2one(
            'crm.claim.category',
            string='Parent category'),
        'line_categories': fields.one2many(
            'crm.claim.line.category',
            'parent_claim_categ_id',
            string='Child claim line categories'),
        'active': fields.boolean(
            'Active',
            required=True,
            help='Indicates whether this category is available to use.'),
        }

    _defaults = {
        'active': True,
        }

crm_claim_category()


class crm_claim_line_category(osv.osv):
    '''
    CRM claim line category. Users should create an (optionally
    hierachical) list of categories describing different kinds of
    claims that can be made against an item.
    '''
    _name = 'crm.claim.line.category'
    _description = 'Categories of CRM claim items'
    _order = 'parent_claim_categ_id,parent_categ_id,sequence'

    _columns = {
        'name': fields.char(
            'Category',
            required=True,
            size=64),
        'sequence': fields.integer(
            'Sequence'),
        'parent_categ_id': fields.many2one(
            'crm.claim.line.category',
            string='Parent category'),
        'parent_claim_categ_id': fields.many2one(
            'crm.claim.category',
            string='Parent claim category'),
        'active': fields.boolean(
            'Active',
            required=True,
            help='Indicates whether this category is available to use.'),
        }

    _defaults = {
        'active': True,
        }

crm_claim_line_category()


class crm_claim_line(osv.osv):
    '''
    CRM claim line. This model links to an individual item in a claim
    by storing the res_id of that item and retrieving the model name
    from its parent claim.
    '''
    _name = 'crm.claim.line'
    _description = 'An individual item in a claim'
    _order = 'name'

    def _get_name(self, cr, uid, ids, field_name, args, context=None):
        return dict([(id, 'claim line #%s' % (id,)) for id in ids])
        # return dict([(line.id, '%s %s' % (line.id, repr(line.resource)))
        #              for line in self.browse(cr, uid, ids, context=context)])

    def _get_model(self, cr, uid, ids, field_name, args, context=None):
        res = {}
        for id in ids:
            res[id] = False
        for line in self.browse(cr, uid, ids, context=context):
            res[line.id] = line.order_claim_id.issue_model
        return res

    ## Attempting to implement better arbitrary model linking than fields.reference
    # def _write_resource(self, cr, uid, ids, field_name, field_value, arg, context=None):
    #     pass

    # def _search_resource(self, cr, uid, obj, field_name, args, context=None):
    #     model = self._get_model(cr, uid, ids, field_name, arg, context=context)[ids[0]]
    #     obj = self.pool.get(model)
    #     res = obj.search(cr, uid, args, context=context)
    #     if res:
    #         return [('id','in',res)]
    #     else:
    #         return [('id','=',0)]

    _columns = {
        'name': fields.function(
            _get_name,
            type='char',
            string='Name',
            method=True,
            store=True),
        'model': fields.function(
            _get_model,
            type='char',
            string='Model',
            method=True,
            readonly=True),
        'resource': fields.reference(
            'Resource',
            selection=crm._links_get,
            size=128),
        'non_item_issue': fields.boolean(
            'Issue not related to any item?'),
        ## Attempting to implement better arbitrary model linking than fields.reference
        # 'res_id': fields.integer(
        #     'Item ID'),
        # 'ref': fields.reference(
        #     'Item',
        #     selection=_get_model  # Can't do this because the selection method is not passed the resource id of self
        # 'res_id': fields.function(
        #         fnct=_get_resource,          # Can't do this because relation has to be known at compile-time
        #         #fnct_inv=_write_resource,
        #         fnct_search=_search_resource,
        #         type='many2one',
        #         relation='',
        #         method=True,
        #         required=True,
        #         string='Item'),
        'claim_id': fields.many2one(
            'crm.claim',
            string='Claim',
            ondelete='cascade'),
        'category': fields.many2one(
            'crm.claim.line.category',
            string='Category'),
        'reason': fields.many2one(
            'crm.claim.line.category',
            string='Reason'),
        'state': fields.selection(
            selection=[('draft', 'Draft'),
                       ('confirm', 'Confirm'),
                       ('cancel', 'Cancel')],
            string='State'),
        'resolution_id': fields.many2one(
            'crm.claim.resolution',
            string='Resolution')
        }

    _defaults = {
        'state': 'draft',
        'non_item_issue': False,
        }

crm_claim_line()


class crm_claim_resolution(osv.osv):
    '''
    CRM claim resolution. This model encapsulates different kinds of
    resolutions for a claim. It's effectively an alternative to
    crm.claim's stages mechanism by allowing steps for resolving a
    claim to be decoupled from claims themselves.
    '''
    _name = 'crm.claim.resolution'
    _description = 'A claim resolution type'

    _columns = {
        'claim_id': fields.many2one(
            'crm.claim',
            string='Claim',
            required=True),
        'state': fields.selection(
            selection=[('draft', 'Draft'),
                       ('open', 'Open'),
                       ('processing', 'Processing'),
                       ('resolved', 'Resolved'),
                       ('cancel', 'Cancelled')],
            string='State',
            required=True),
        'description': fields.text(
            'Description'),
        }

    def wkf_next(self, cr, uid, ids, context=None):
        '''
        This method advances the state to the next state.
        '''
        self.action_next(cr, uid, ids, context=context)

    def action_next(self, cr, uid, ids, context=None):
        for resolution in self.browse(self, cr, uid, ids, context=context):
            # FIXME
            resolution.state = STATES[STATES.index(cmp=lambda s: s[0] == resolution.state) + 1]

    def wkf_previous(self, cr, uid, ids, context=None):
        '''
        This method retrogrades the state to the previous state.
        '''
        self.action_previous(cr, uid, ids, context=context)

    def action_previous(self, cr, uid, ids, context=None):
        for resolution in self.browse(self, cr, uid, ids, context=context):
            # FIXME
            resolution.state = STATES[STATES.index(cmp=lambda s: s[0] == resolution.state) - 1]

    def wkf_open(self, cr, uid, ids, context=None):
        self.action_open(cr, uid, ids, context=context)

    def action_open(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, vals={'state': 'open'}, context=context)

    def wkf_process(self, cr, uid, ids, context=None):
        self.action_process(cr, uid, ids, context=context)

    def action_process(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, vals={'state': 'processing'}, context=context)

    def wkf_resolve(self, cr, uid, ids, context=None):
        self.action_resolve(cr, uid, ids, context=context)

    def action_resolve(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, vals={'state': 'resolve'}, context=context)

    def wkf_cancel(self, cr, uid, ids, context=None):
        self.action_cancel(cr, uid, ids, context=context)

    def action_cancel(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, vals={'state': 'cancel'}, context=context)


crm_claim_resolution()

class crm_claim_line_resolution(osv.osv):
    _inherit = 'crm.claim.resolution'
    _name = 'crm.claim.line.resolution'

    _columns = {
        'claim_line_id': fields.many2one(
            'crm.claim.line',
            string='Claim line',
            required=True),
        'claim_id': fields.related(
            'claim_line_id', 'claim_id',
            relation='crm.claim',
            string='Claim',
            readonly=True),
        }
