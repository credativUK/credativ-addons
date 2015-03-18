# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution    
#    Copyright (C) 2015 credativ Ltd (<http://credativ.co.uk>).
#    All Rights Reserved
#    $Id$
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

from openerp.osv import fields, osv
from datetime import datetime
from dateutil.relativedelta import relativedelta


class account_payment_term_line(osv.osv):
    _inherit = 'account.payment.term.line'

    _columns = {
                'specific_date': fields.date('Specific Date', help="Select a specific payment date to take precedence over other computations")
    }

class account_payment_term(osv.osv):
    _inherit = 'account.payment.term'

    def compute(self, cr, uid, id, value, date_ref=False, context=None):
        '''
        Use specific date set on payment term lines in order to determine payment due dates.
        It is not simple to alter the values returned from super(account_payment_term, self).compute(...), so overwritting function instead
        '''
        if context is None:
            context = {}
        if not date_ref:
            date_ref = datetime.now().strftime('%Y-%m-%d')
        pt = self.browse(cr, uid, id, context=context)
        amount = value
        result = []
        obj_precision = self.pool.get('decimal.precision')
        prec = obj_precision.precision_get(cr, uid, 'Account')
        for line in pt.line_ids:
            if line.value == 'fixed':
                amt = round(line.value_amount, prec)
            elif line.value == 'procent':
                amt = round(value * line.value_amount, prec)
            elif line.value == 'balance':
                amt = round(amount, prec)
            if amt:
                if line.specific_date:
                    next_date = datetime.strptime(line.specific_date, '%Y-%m-%d')
                else:
                    next_date = (datetime.strptime(date_ref, '%Y-%m-%d') + relativedelta(days=line.days))
                    if line.days2 < 0:
                        next_first_date = next_date + relativedelta(day=1,months=1) #Getting 1st of next month
                        next_date = next_first_date + relativedelta(days=line.days2)
                    if line.days2 > 0:
                        next_date += relativedelta(day=line.days2, months=1)
                result.append( (next_date.strftime('%Y-%m-%d'), amt) )
                amount -= amt

        amount = reduce(lambda x,y: x+y[1], result, 0.0)
        dist = round(value-amount, prec)
        if dist:
            result.append( (time.strftime('%Y-%m-%d'), dist) )
        return result

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
