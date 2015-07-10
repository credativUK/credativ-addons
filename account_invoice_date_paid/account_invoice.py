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

from openerp.osv import osv, fields
from datetime import datetime


class AccountInvoice(osv.Model):

    _name = 'account.invoice'
    _inherit = 'account.invoice'


    def confirm_paid(self, cr, uid, ids, context=None):
        res = super(AccountInvoice, self).confirm_paid(cr, uid, ids, context=context)
        self.write(cr, uid, ids, {'date_paid':datetime.now()}, context=context)
        return res


    _columns = {
            'date_paid' : fields.datetime('Date Paid', help='The date that the invoice became \'paid\' in the system.'),
    }

