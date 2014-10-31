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
import re

class AccountFollowupPrint(osv.TransientModel):
    _inherit = 'account_followup.print'

    def process_partners(self, cr, uid, partner_ids, data, context=None):
        ctx = context and context.copy() or {}
        ctx.setdefault('account_followup_skip_partners', True)
        res = super(AccountFollowupPrint, self).process_partners(cr, uid, partner_ids, data, context=ctx)
        res['resulttext'] = re.sub(r'had unknown email address\(es\)', r'were not set to email followups or had unknown email address(es)', res.get('resulttext',''))
        return res
