# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 credativ Ltd (<http://credativ.co.uk>).
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

from openerp.osv import osv
from openerp.tools.translate import _


class crm_claim(osv.Model):

    _inherit = 'crm.claim'

    def get_root_partner(self, cr, uid, partner_id, context=None):
        '''This function finds the root partner of a given partner ID.
           :param partner_id: Partner ID
        '''

        def root_partner(partner):
            ''' Recursive function to find the root of a partner-tree.'''

            if partner.parent_id:
                return root_partner(partner.parent_id)
            return partner

        if context is None:
            context = {}

        partner = self.pool.get('res.partner').browse(cr, uid, partner_id,
                                                      context=context)

        return root_partner(partner).id

    def onchange_partner_id(self, cr, uid, ids, partner_id, email=False):
        """This function returns value of partner address based on partner
           :param part: Partner's id
           :param email: ignored
        """

        warning = {}
        context = {}
        res = super(crm_claim, self).onchange_partner_id(cr, uid, ids,
                                                         partner_id,
                                                         email=email)

        if partner_id:
            root_partner_id = self.get_root_partner(cr, uid, partner_id,
                                                         context=context)
            partner_claim_ids = self.search(cr, uid,
                                            [('partner_id',
                                              'child_of',
                                              [root_partner_id]),
                                             ('state', 'in', ['open',
                                                              'draft']),
                                             ('id', 'not in', ids)])

            if partner_claim_ids:
                claims = self.read(cr, uid, partner_claim_ids, ['number'])
                claims_str = '\n\n'.join('%s' % (claim['number'])
                                         for claim in claims)
                warning = {
                    'title': _('Warning!'),
                    'message': _('There are draft / open claims for this partner:\n\n%s'
                                 % (claims_str))
                }
        res['warning'] = warning
        return res
