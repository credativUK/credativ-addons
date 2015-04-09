# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 credativ ltd (<http://www.credativ.co.uk>). All Rights Reserved
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

from openerp.osv.orm import Model, fields
from openerp.tools.translate import _


class CreditControlRun(Model):

    _inherit = 'credit.control.run'

    _columns = {
        'partner_filter_id': fields.many2one('ir.filters',
                                             'Partner Filter',
                                             domain=[('model_id',
                                                      '=',
                                                      'res.partner')],
                                             help=_("Select a filter for partners. New filter can be created from the customers screen.")),

        }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
