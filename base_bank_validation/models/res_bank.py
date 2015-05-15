# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 credativ Ltd (<http://credativ.co.uk>).
#    All Rights Reserved
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

import re
from openerp import models, api, _
from openerp.exceptions import Warning


class PartnerBank(models.Model):
    '''Bank Accounts'''

    _inherit = "res.partner.bank"

    CHECK_BANK_TYPE = ['bank']

    @api.constrains('acc_number', 'country_id')
    def _check_bank_account_format(self):
        if(
            self.state in self.CHECK_BANK_TYPE and self.country_id and
            self.country_id.bank_regex
        ):
            if not re.match(self.country_id.bank_regex, self.acc_number):
                raise Warning(_('Invalid Bank account number'))


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
