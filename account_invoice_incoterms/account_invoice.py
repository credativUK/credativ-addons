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

from openerp import fields, models, api

class account_invoice(models.Model):
    _inherit = 'account.invoice'
    
    incoterm = fields.Many2one(comodel_name='stock.incoterms', compute='_compute_incoterm')
    
    @api.one
    def _compute_incoterm(self):
        res = {}
        inv_id = self.id
        cr = self.env.cr

        so_line_query = '''SELECT DISTINCT incoterm
                            FROM sale_order
                            WHERE id IN
                                (SELECT DISTINCT order_id
                                FROM sale_order_line
                                WHERE id IN
                                    (SELECT DISTINCT order_line_id
                                    FROM sale_order_line_invoice_rel
                                    WHERE invoice_id = %s))''' % (inv_id)

        so_query      = '''SELECT DISTINCT incoterm
                            FROM sale_order
                            WHERE id IN
                                (SELECT DISTINCT order_id
                                FROM sale_order_invoice_rel
                                WHERE invoice_id = %s)''' % (inv_id)

        po_line_query = '''SELECT DISTINCT incoterm_id
                            FROM purchase_order
                            WHERE id IN
                                (SELECT DISTINCT order_id
                                FROM purchase_order_line
                                WHERE id IN
                                    (SELECT DISTINCT order_line_id
                                    FROM purchase_order_line_invoice_rel
                                    WHERE invoice_id IN
                                        (SELECT DISTINCT id
                                        FROM account_invoice_line
                                        WHERE invoice_id = %s)))''' % (inv_id)

        incoterm_ids = []

        cr.execute(so_line_query)
        incoterm_ids.extend([i[0] for i in cr.fetchall() if i[0] != None])
        cr.execute(so_query)
        incoterm_ids.extend([i[0] for i in cr.fetchall() if i[0] != None])
        cr.execute(po_line_query)
        incoterm_ids.extend([i[0] for i in cr.fetchall() if i[0] != None])

        self.incoterm = incoterm_ids and incoterm_ids[0] or False

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
