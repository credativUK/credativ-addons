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
from decimal_precision import decimal_precision as dp

class sale_order_claim(osv.osv):
    '''
    This class allows a refund and a voucher to be issued against a
    sale.order.claim. It also adds some refund and voucher
    calculations to sale.order.claims.
    '''
    _inherit = 'sale.order.claim'

    def _total_refund(self, cr, uid, ids, field_name, arg, context=None):
        '''Calculates the sum of all the refunds for this claim'''
        if isinstance(ids, (int, long)):
            ids = [ids]

        claim_pool = self.pool.get('sale.order.claim')

        return dict([(claim.id, sum([claim.refund] + [issue.refund for issue in claim.order_issue_ids]))
                     for claim in claim_pool.browse(cr, uid, ids, context=context)])

    def _total_voucher(self, cr, uid, ids, field_name, arg, context=None):
        '''Calculates the sum of all the vouchers for this claim'''
        if isinstance(ids, (int, long)):
            ids = [ids]

        claim_pool = self.pool.get('sale.order.claim')

        return dict([(claim.id, sum([claim.voucher] + [issue.voucher for issue in claim.order_issue_ids]))
                     for claim in claim_pool.browse(cr, uid, ids, context=context)])

    def _prev_compensation(self, cr, uid, ids, compensation_type=['refund','voucher'], claim_state=('processed',), context=None):
        '''Calculates the sum of all compensations of the specified
        type(s) made against the same sale.order as this claim and for
        claims in the specified state(s)'''
        if isinstance(ids, (int, long)):
            ids = [ids]

        res = {}

        order_claims_pool = self.pool.get('sale.order.claim')

        for id in ids:
            sale_order_id = self.browse(cr, uid, id, context=context).sale_order_id.id
            claim_ids = order_claims_pool.search(cr, uid, [('sale_order_id','=',sale_order_id),
                                                           ('id','<>',id),
                                                           ('state','in',claim_state)], context=context)
            res[id] = float(sum([sum([getattr(claim, 'total_%s' % (comp_type,))
                                      for comp_type in compensation_type])
                                 for claim in order_claims_pool.browse(cr, uid, claim_ids, context=context)]))

        return res

    def _prev_refund(self, cr, uid, ids, field_name, arg, context=None):
        '''Calculates the sum of all refunds made against the same
        sale.order as this claim'''
        return self._prev_compensation(cr, uid, ids,
                                       compensation_type=['refund'],
                                       claim_state=('processed',),
                                       context=context)

    def _prev_voucher(self, cr, uid, ids, field_name, arg, context=None):
        '''Calculates the sum of all vouchers issued against the same
        sale.order as this claim'''
        return self._prev_compensation(cr, uid, ids,
                                       compensation_type=['voucher'],
                                       claim_state=('processed',),
                                       context=context)

    def _pending_refund(self, cr, uid, ids, field_name, arg, context=None):
        '''Calculates the sum of all refunds that have been requested
        against the same sale.order as this claim (but not yet
        processed)'''
        return self._prev_compensation(cr, uid, ids,
                                       compensation_type=['refund'],
                                       claim_state=('open-vouchers','open-refunds','rejected'),
                                       context=context)

    def _pending_voucher(self, cr, uid, ids, field_name, arg, context=None):
        '''Calculates the sum of all the vouchers that have been
        requested against the same sale.order as this claim (but not
        yet processed)'''
        return self._prev_compensation(cr, uid, ids,
                                       compensation_type=['voucher'],
                                       claim_state=('open-vouchers','open-refunds','rejected'),
                                       context=context)

    def _max_refundable(self, cr, uid, ids, field_name, arg, context=None):
        '''Calculates the maximum that may be refunded against this
        sale.order; defined as the difference between the sale.order
        total and the sum of previous and pending refunds (and not
        vouchers)'''
        if isinstance(ids, (int, long)):
            ids = [ids]
        return dict([(claim.id, claim.order_total - self._prev_compensation(cr, uid, claim.id,
                                                                            compensation_type=['refund'],
                                                                            claim_state=('open-vouchers','open-refunds','rejected','processed'),
                                                                            context=context)[claim.id])
                     for claim in self.browse(cr, uid, ids, context=context)])

    def _sum_compensation(self, cr, uid, ids, refund, voucher, issue_ids, context=None):
        '''
        Returns a tuple: the sum of the manual refund and all the refunds in the
        given issues, and the sum of the given voucher and all the vouchers in the
        given issues.
        '''
        return (refund + sum([issue[2].get('refund', 0.0) for issue in issue_ids if issue[0] in [0,1]]),
                voucher + sum([issue[2].get('voucher', 0.0) for issue in issue_ids if issue[0] in [0,1]]))

    def _enforce_max_compensation(self, cr, uid, ids, context=None):
        '''Implements the constraint that refunds/voucher amount must not
        exceed maximum refundable amount.
        '''
        for claim in self.browse(cr, uid, ids, context=context):
            if claim.total_refund + claim.total_voucher > claim.max_refundable:
                return False
        return True

    def _draft_amounts(self, cr, uid, sale_order_id, order_issue_ids, context=None):
        '''
        This method calculates the previous, pending, and maximum
        amounts for claims that are in draft (i.e. for which no ids
        yet exist).
        '''
        so_pool = self.pool.get('sale.order')
        sale_order = so_pool.browse(cr, uid, sale_order_id, context=context)

        def claim_total_compensation(comp_type):
            # FIXME You need to get the current claim.refund and
            # claim.voucher values; they should be passed as
            # arguments to this onchange
            return sum([issue.get(comp_type, 0.0) for (_, _, issue) in order_issue_ids if issue])
        
        def so_total_compensation(sale_order_id, comp_type, claim_state=('processed',)):
            claim_ids = self.search(cr, uid, [('sale_order_id','=',sale_order_id),
                                              ('state','in',claim_state)], context=context)
            return sum([sum([getattr(claim, 'total_%s' % (ct,))
                             for ct in comp_type])
                        for claim in self.browse(cr, uid, claim_ids, context=context)])

        return {
            'total_refund':
                claim_total_compensation('refund'),
            'total_voucher':
                claim_total_compensation('voucher'),
            'prev_refund':
                so_total_compensation(sale_order_id, ['refund'], claim_state=('processed',)),
            'prev_voucher':
                so_total_compensation(sale_order_id, ['voucher'], claim_state=('processed',)),
            'pending_refund':
                so_total_compensation(sale_order_id, ['refund'], claim_state=('open-vouchers','open-refunds')),
            'pending_voucher':
                so_total_compensation(sale_order_id, ['voucher'], claim_state=('open-vouchers','open-refunds')),
            'max_refundable':
                sale_order.amount_total - so_total_compensation(sale_order_id, ['refund'],
                                                                claim_state=('open-vouchers','open-refunds','processed')),
            }

    def _get_claims_from_issues(self, cr, uid, ids, context=None):
        issue_pool = self.pool.get('sale.order.issue')
        return list(set([issue['order_claim_id'][0] for issue in issue_pool.read(cr, uid, ids, ['order_claim_id'], context=context)]))

    _columns = {
        'total_refund': fields.function(
            _total_refund,
            type='float',
            string='Total refunded',
            readonly=True,
            store={
                'sale.order.claim': (lambda self, cr, uid, ids, ctx: ids, ['refund'], 10),
                'sale.order.issue': (_get_claims_from_issues , ['refund'], 10)
                }),
        'total_voucher': fields.function(
            _total_voucher,
            type='float',
            string='Total vouchers',
            readonly=True,
            store={
                'sale.order.claim': (lambda self, cr, uid, ids, ctx: ids, ['voucher'], 10),
                'sale.order.issue': (_get_claims_from_issues , ['voucher'], 10)
                }),
        'prev_refund': fields.function(
            _prev_refund,
            type='float',
            string='Previous refunds',
            readonly=True),
        'prev_voucher': fields.function(
            _prev_voucher,
            type='float',
            string='Previous vouchers',
            readonly=True),
        'pending_refund': fields.function(
            _pending_refund,
            type='float',
            string='Pending refunds',
            readonly=True),
        'pending_voucher': fields.function(
            _pending_voucher,
            type='float',
            string='Pending vouchers',
            readonly=True),
        'max_refundable': fields.function(
            _max_refundable,
            type='float',
            string='Maximum refundable',
            readonly=True),
        'refund': fields.float(
            'Refund',
            digits_compute=dp.get_precision('Sale Price'),
            readonly=True,
            states={'draft': [('readonly', False)]}),
        'voucher': fields.float(
            'Voucher',
            digits_compute=dp.get_precision('Sale Price'),
            readonly=True,
            states={'draft': [('readonly', False)]}),
        'voucher_code': fields.char(
            'Voucher code',
            size=128),
        }

    _constraints = [
        (_enforce_max_compensation, 'Compensation amount exceeds maximum allowed for this order.', ['total_refund', 'total_voucher']),
    ]

    def onchange_sale_order(self, cr, uid, ids, sale_order_id, order_issue_ids, context=None):
        res = super(sale_order_claim, self).onchange_sale_order(cr, uid, ids, sale_order_id, order_issue_ids, context=context)

        so_pool = self.pool.get('sale.order')
        sale_order = so_pool.browse(cr, uid, sale_order_id, context=context)

        if not sale_order:
            return res

        if isinstance(ids, (list, tuple)):
            id = ids and ids[0] or []
        elif isinstance(ids, (int, long)):
            id = ids

        claim = self.browse(cr, uid, id, context=context)

        if not claim:
            # if the claim is still in draft, get the totals without
            # using the claim object
            res['value'].update(self._draft_amounts(cr, uid, sale_order_id, order_issue_ids, context=context))
        else:
            res['value'].update({
                    'total_refund': self._total_refund(cr, uid, id, field_name='total_refund', arg=None, context=None)[id],
                    'total_voucher': self._total_voucher(cr, uid, id, field_name='total_voucher', arg=None, context=None)[id],
                    'prev_refund': self._prev_refund(cr, uid, id, field_name='prev_refund', arg=None, context=None)[id],
                    'prev_voucher': self._prev_voucher(cr, uid, id, field_name='prev_voucher', arg=None, context=None)[id],
                    'pending_refund': self._pending_refund(cr, uid, id, field_name='pending_refund', arg=None, context=None)[id],
                    'pending_voucher': self._pending_voucher(cr, uid, id, field_name='pending_voucher', arg=None, context=None)[id],
                    'max_refundable': self._max_refundable(cr, uid, id, field_name='max_refundable', arg=None, context=None)[id],
                    })

        return res

    def on_change_claim_refund(self, cr, uid, ids, refund, issue_ids=[], context=None):
        if not ids:
            return {'value': {'total_refund': refund}}
            
        if isinstance(ids, (list, tuple)):
            id = ids[0]
        elif isinstance(ids, (int, long)):
            id = ids

        claim = self.browse(cr, uid, id, context=context)
        total_refund, _ = self._sum_compensation(cr, uid, ids, refund, 0.0, issue_ids, context=context)
        total_refund = round(float(total_refund), 2)
        max_refundable = self._max_refundable(cr, uid, id, 'max_refundable', None, context=None)[id]
        max_refundable = round(float(max_refundable), 2)

        if total_refund > max_refundable:
            return {'warning': {'title': 'Maximum refund',
                                'message': 'The maximum refundable amount for this order is %.2f. The refund %.2f exceeds this maximum.' %\
                                (max_refundable, total_refund)},
                    'value': {'total_refund': total_refund,
                              'max_refundable': max_refundable}}

        return {'value': {'total_refund': total_refund,
                          'max_refundable': max_refundable}}

    def on_change_claim_voucher(self, cr, uid, ids, voucher, issue_ids=[], context=None):
        if not ids:
            return {'value': {'total_voucher': voucher}}

        if isinstance(ids, (list, tuple)):
            id = ids[0]
        elif isinstance(ids, (int, long)):
            id = ids

        claim = self.browse(cr, uid, id, context=context)
        _, total_voucher = self._sum_compensation(cr, uid, ids, 0.0, voucher, issue_ids, context=context)
        total_voucher = round(float(total_voucher), 2)
        max_refundable = self._max_refundable(cr, uid, id, 'max_refundable', None, context=None)[id]
        max_refundable = round(float(max_refundable), 2)

        if total_voucher > max_refundable:
            return {'warning': {'title': 'Maximum voucher',
                                'message': 'The maximum refundable amount for this order is %0.2d. The voucher %0.2d exceeds this maximum.' %\
                                (max_refundable, total_voucher)},
                    'value': {'total_voucher': total_voucher,
                              'max_refundable': max_refundable}}

        return {'value': {'total_voucher': self._total_voucher(cr, uid, id, field_name='total_voucher', arg=None, context=None)[id] + voucher,
                          'max_refundable': self._max_refundable(cr, uid, id, field_name='max_refundable', arg=None, context=None)[id] - voucher}}

    def action_open(self, cr, uid, ids, context=None):
        # TODO What should we do with the refunds/vouchers here?
        return super(sale_order_claim, self).action_open(cr, uid, ids, context=context)

    def action_process(self, cr, uid, ids, context=None):
        # TODO What should we do with the refunds/vouchers here?
        return super(sale_order_claim, self).action_process(cr, uid, ids, context=context)

    def action_reject(self, cr, uid, ids, context=None):
        # TODO What should we do with the refunds/vouchers here?
        return super(sale_order_claim, self).action_reject(cr, uid, ids, context=context)

    def action_cancel(self, cr, uid, ids, context=None):
        # TODO What should we do with the refunds/vouchers here?
        return super(sale_order_claim, self).action_cancel(cr, uid, ids, context=context)

sale_order_claim()


class sale_order_issue(osv.osv):
    '''
    This class allows a refund and a voucher to be issued against a
    sale.order.issue. It also adds some refund and voucher
    calculations to sale.order.issues.
    '''
    _inherit = 'sale.order.issue'

    def __prev_compensation(self, cr, uid, ids, compensation_type=['refund','voucher'], claim_state=('processed',), context=None):
        '''Calculates the sum of all compensation of the specified
        type made against sale.order.issues which are themselves
        against the same resource as this sale.order.claim and where
        the parent sale.order.claim's state matches the given claim
        state(s).'''
        res = {}

        for issue in self.browse(cr, uid, ids, context=context):
            issue_ids = self.search(cr, uid, [('resource','=','%s,%s' % (issue.resource._table._name, issue.resource.id)),
                                              ('state','not in',['draft','rejected']),
                                              ('id','<>',issue.id)], context=context)
            res[issue.id] = float(sum([float(sum([getattr(iss, comp_type)
                                                  for comp_type in compensation_type]))
                                       for iss in self.browse(cr, uid, issue_ids, context)
                                       if iss.order_claim_id.state in claim_state]))
        return res

    def _prev_compensation(self, cr, uid, ids, field_name, arg, context=None):
        return self.__prev_compensation(cr, uid, ids,
                                        compensation_type=['refund','voucher'],
                                        claim_state=('processed',),
                                        context=context)

    def _prev_refund(self, cr, uid, ids, field_name, arg, context=None):
        '''Calculates the sum of all refunds made against the same
        sale.order as this claim'''
        return self.__prev_compensation(cr, uid, ids,
                                        compensation_type=['refund'],
                                        claim_state=('processed',),
                                        context=context)

    def _prev_voucher(self, cr, uid, ids, field_name, arg, context=None):
        '''Calculates the sum of all vouchers issued against the same
        sale.order as this claim'''
        return self.__prev_compensation(cr, uid, ids,
                                        compensation_type=['voucher'],
                                        claim_state=('processed',),
                                        context=context)

    def _max_refundable(self, cr, uid, ids, field_name, args, context=None):
        raise NotImplementedError('sale_order_issue._max_refundable must be provided for derived classes.')

    def _sum_compensation(self, cr, uid, ids, refund, voucher, issue_ids, context=None):
        '''
        Returns a tuple: the sum of the manual refund and all the refunds in the
        given issues, and the sum of the given voucher and all the vouchers in the
        given issues.
        '''
        return (refund + sum([issue[2].get('refund', 0.0) for issue in issue_ids if issue[0] in [0,1]]),
                voucher + sum([issue[2].get('voucher', 0.0) for issue in issue_ids if issue[0] in [0,1]]))

    _columns = {
        'refund': fields.float(
            'Refund',
            digits_compute=dp.get_precision('Sale Price')),
        'voucher': fields.float(
            'Voucher',
            digits_compute=dp.get_precision('Sale Price')),
        'prev_compensation': fields.function(
            _prev_compensation,
            type='float',
            string='Compensated',
            method=True,
            store=False,
            readonly=True),
        'max_refundable': fields.function(
            _max_refundable,
            type='float',
            string='Maximum refund',
            readonly=True),
        }

    def on_change_refund(self, cr, uid, ids, refund, order_issue_ids, context=None):
        if not ids:
            return {'value': {'total_refund': refund}}

        if isinstance(ids, (list, tuple)):
            id = ids[0]
        elif isinstance(ids, (int, long)):
            id = ids

        issue = self.browse(cr, uid, id, context=context)
        refund, _ = self._sum_compensation(cr, uid, id, refund, 0.0, order_issue_ids, context=context)
        refund = round(float(refund), 2)

        import pdb; pdb.set_trace()

        if refund > round(float(issue.order_claim_id.max_refundable), 2):
            return {'warning': {'title': 'Maximum compensation',
                                'message': 'The maximum refundable amount for this order is %.2f. The refund %.2f exceeds this maximum.' %\
                                (round(float(issue.order_claim_id.max_refundable), 2), refund)}}
        if refund > round(float(issue.max_refundable), 2):
            return {'warning': {'title': 'Maximum compensation',
                                'message': 'The maximum refundable amount for this item is %.2f. The refund %.2f exceeds this maximum.' %\
                                (round(float(issue.max_refundable), 2), refund)}}

        return {'value': {'total_refund': issue.order_claim_id.total_refund + refund}}

    def on_change_voucher(self, cr, uid, ids, voucher, order_issue_ids, context=None):
        if not ids:
            return {'value': {'total_voucher': voucher}}

        if isinstance(ids, (list, tuple)):
            id = ids[0]
        elif isinstance(ids, (int, long)):
            id = ids

        issue = self.browse(cr, uid, id, context=context)
        _, voucher = self._sum_compensation(cr, uid, id, 0.0, voucher, order_issue_ids, context=context)
        voucher = round(float(voucher), 2)

        if voucher > round(float(issue.order_claim_id.max_refundable), 2):
            return {'warning': {'title': 'Maximum compensation',
                                'message': 'The maximum refundable amount for this order is %.2f. The voucher %.2f exceeds this maximum.' %\
                                (round(float(issue.order_claim_id.max_refundable), 2), voucher)}}
        if voucher > round(float(issue.max_refundable), 2):
            return {'warning': {'title': 'Maximum compensation',
                                'message': 'The maximum refundable amount for this item is %.2f. The voucher %.2f exceeds this maximum.' %\
                                (round(float(issue.max_refundable), 2), voucher)}}

        return {'value': {'total_voucher': issue.order_claim_id.total_voucher + voucher}}

sale_order_issue()


class sale_order(osv.osv):
    '''
    Add columns to sale.order to sum the total compensation paid out
    against the order.
    '''
    _inherit = 'sale.order'

    def _total_compensation(self, cr, uid, ids, compensation_type=['refund','voucher'], claim_state=('processed',), context=None):
        '''Calculates the sum of all compensations of the specified
        type(s) and in the specified state(s) made against this
        sale.order'''
        if isinstance(ids, (int, long)):
            ids = [ids]

        res = {}

        order_claims_pool = self.pool.get('sale.order.claim')

        for id in ids:
            claim_ids = order_claims_pool.search(cr, uid, [('sale_order_id','=',id),
                                                           ('state','in',claim_state)], context=context)
            res[id] = sum([sum([getattr(claim, 'total_%s' % (comp_type,))
                                for comp_type in compensation_type])
                           for claim in order_claims_pool.browse(cr, uid, claim_ids, context)])

        return res

    def _total_refund(self, cr, uid, ids, field_name, arg, context=None):
        '''Calculates the sum of all refunds made against this
        sale.order'''
        return self._total_compensation(cr, uid, ids,
                                        compensation_type=['refund'],
                                        claim_state=('processed',),
                                        context=context)

    def _total_voucher(self, cr, uid, ids, field_name, arg, context=None):
        '''Calculates the sum of all vouchers issued against this
        sale.order'''
        return self._total_compensation(cr, uid, ids,
                                        compensation_type=['voucher'],
                                        claim_state=('processed',),
                                        context=context)

    _columns = {
        # FIXME Consider storing these as their calculation requires
        # at least four inner loops and it will make generating the
        # list view of sale orders take even longer
        'total_refund': fields.function(
            _total_refund,
            type='float',
            string='Refunded',
            readonly=True),
        'total_voucher': fields.function(
            _total_voucher,
            type='float',
            string='Vouchers',
            readonly=True),
        }
