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

from openerp import fields, models


class Country(models.Model):

    _inherit = 'res.country'

    bank_regex = fields.Char('Bank account Regex', help="Validate normal bank "
                             "account type by Python Regex expression.\n e.g "
                             "for uk bank account 00-00-00 12345678 use regex "
                             "^\d{2}-\d{2}-\d{2}\s\d{8}$")


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
