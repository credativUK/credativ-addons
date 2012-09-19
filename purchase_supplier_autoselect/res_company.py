# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2012 credativ Ltd (<http://credativ.co.uk>).
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
from tools.translate import _

class res_company(osv.osv):
    _inherit = "res.company"

    _columns = {
        'po_name_regex': fields.char('Purchase Order Reference Format', size=64, help="The regex used to match the supplier reference to the PO name. eg (?<=^.{2}).{3}  will get the 3rd, 4th and 5th characters as the supplier reference."),
    }
    
    _defaults = {
        'po_name_regex': '(?<=^.{2}).{3}'
    }

res_company()