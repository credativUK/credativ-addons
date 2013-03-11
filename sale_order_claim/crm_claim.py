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
        'claim_line_ids': fields.one2many(
            'crm.claim.line',
            'claim_id',
            string='Claim items'),
        'category': fields.many2one(
            'crm.claim.category',
            string='Category'),
        'reason': fields.many2one(
            'crm.claim.category',
            string='Reason'),
        }

    def claim_lines_from_all(self, cr, uid, ids, res_ids, context=None):
        '''
        This method creates claim lines for all the given res_ids
        (which should be resources of the claim_lines_ref model).
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
    _order = 'sequence'

    _columns = {
        'name': fields.char(
            'Name',
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
    _order = 'sequence'

    _columns = {
        'name': fields.char(
            'Name',
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
        pass

    def _get_claim_resource(self, cr, uid, ids, context=None):
        if isinstance(ids, (list, tuple)):
            a = ids[0]
        else:
            a = ids
        claim_ref = self.browse(cr, uid, a, context=context).claim_id.claim_lines_model_id.ref
        model, res_id = claim_ref.split(',')
        return (model, int(res_id))
        
    def _get_model(self, cr, uid, ids, field_name, args, context=None):
        model, res_id = self._get_claim_resource(cr, uid, ids, context=context)
        return dict([(id, model) for id in ids])

    def _get_resource(self, cr, uid, ids, field_name, arg, context=None):
        model = self._get_model(cr, uid, ids, field_name, arg, context=context)[ids[0]]
        obj = self.pool.get(model)
        return obj.browse(cr, uid, [l['res_id'] for l in self.read(cr, uid, ids, ['res_id'], context=context)], context=context)

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
            method=True,
            readonly=True,
            store=False),
        'resource': fields.reference(
            'Resource',
            selection=crm._links_get,
            size=128),
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
                required=True),
        'category': fields.many2one(
                'crm.claim.line.category',
                required=True,
                string='Category'),
        'reason': fields.many2one(
                'crm.claim.line.category',
                required=True,
                string='Reason'),
        }

crm_claim_line()
