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

from osv import osv, fields

class PurchaseOrder(osv.Model):
    _inherit = 'purchase.order'

    _columns = {
            'procurements_auto_allocate': fields.boolean('Auto Allocate Procurements', help='If this option is enabled and there are purchase lines not allocated to any procurements, '\
                                                                                           'the procurement scheduler will attempt to automatically allocate procurements to them.'),
        }

    _defaults = {
            'procurements_auto_allocate': True,
        }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
