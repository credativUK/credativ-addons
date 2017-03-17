# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2017 credativ Ltd (<http://credativ.co.uk>).
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
from osv import fields, osv
import time
import re
import netsvc

class quotation_wizard(osv.osv_memory):
    _inherit = 'quotation.wizard'

    def assign_new_prices(self, cr, uid, old_quotation_obj, quotation_obj, contract_id, assignment_obj):
        """Changes running assignment & contract prices due to revised quotation"""
        assignment_obj.write({'name': quotation_obj.name,
                                                'description': quotation_obj.description,
                                                'ref': quotation_obj.name,
                                                'value': quotation_obj.tot_value,
                                                'service_quote_id': quotation_obj.id,
        })
        ammendment_pool = self.pool.get('contract.ammendment')
        if contract_id:
            contract_obj = self.pool.get('pc_contractor.contract').browse(cr, uid, contract_id)
            if contract_obj.state == 'running' or (contract_obj.state == 'caretake' and contract_obj.caretake_draft == False):
                sale_invoice_amount = contract_obj.sale_invoice_amount
            else:
                sale_invoice_amount = quotation_obj.tot_value * (quotation_obj.contract_assignment_id.company_id.co_prop_sale_mul or 4.0)
            if contract_obj.state == 'running' or (contract_obj.state == 'caretake' and contract_obj.caretake_draft == False):
                original_loan_amount = contract_obj.original_loan_amount
            else:
                original_loan_amount = sale_invoice_amount * (1 + (quotation_obj.contract_assignment_id.company_id.vat_tax) / 100)
            sales_credit = self.pool.get('pc_contract.assignment').get_sales_credit(time.strftime('%Y-%m-%d'), quotation_obj.contract_assignment_id.start_date, sale_invoice_amount)
            contract_obj.write({'monthly_billing': quotation_obj.tot_value,
                                'variable_charge': quotation_obj.tot_value * (quotation_obj.contract_assignment_id.company_id.co_prop_month_pcnt or 20.0) / 100.0,
                                'cleans_per_month': quotation_obj.freq_id.frequency,
                                'sale_invoice_amount': sale_invoice_amount,
                                'sales_credit': sales_credit,
                                'original_loan_amount': original_loan_amount,
                                })
            if old_quotation_obj.freq_id.id != quotation_obj.freq_id.id:
                ammendment_pool.create(cr, uid, {'contract_id': contract_id,
                                                'user_id': uid,
                                                'date_change': time.strftime('%Y-%m-%d'),
                                                'description': 'Frequency changed from %s to %s' % (old_quotation_obj.freq_id.name, quotation_obj.freq_id.name)})

    def confirm(self, cr, uid, ids, context={}):
        quotation_pool = self.pool.get('service.quotation')
        for wizard in self.browse(cr, uid, ids, context=context):
            quotation_obj = quotation_pool.browse(cr, uid, context['active_id'], context=context)
            contract_id = quotation_obj.contract_assignment_id.current_contract_id.id
            if not contract_id and any([x.state == 'expired' for x in quotation_obj.contract_assignment_id.contractor_contract_ids]):
                raise osv.except_osv('Error!', "Cannot revise a quotation for expired contract")
            name = quotation_obj.name
            base_name = re.sub(r'\((revised|current)\)*', '', name)
            new_name = base_name + '(revised)'
            # Calculate the new version numbers
            cr.execute('SELECT id, version FROM service_quotation WHERE name ~ %s ', (base_name,))
            max_version, max_ids = 0, []
            for row in cr.dictfetchall():
                if row['version'] == max_version:
                    max_ids.append(row['id'])
                elif row['version'] > max_version:
                    max_version = row['version']
                    max_ids = [row['id'],]
            version_revised = max_version + 1
            # End calculate new version numbers
            quotation_obj.write({'name': new_name, 'state':'revised'})
            vals = {'name': re.sub(r'\((revised|current)\)*', '', name) + '(current)',
                    'description': wizard.description,
                    'freq_id': wizard.frequency_id.id,
                    'version': version_revised, # This will be auto-incremented by 1 somewhere else
                    'tot_value': wizard.price,
                    'parent_id':quotation_obj.parent_id and quotation_obj.parent_id.id or context['active_id'],
                    }
            new_quotation_id = quotation_pool.copy(cr, uid, quotation_obj.id, default=vals)
            new_quotation_obj = quotation_pool.browse(cr, uid, new_quotation_id)
            new_quotation_obj.write({'contract_assignment_id':False,
            })
            wf_service = netsvc.LocalService('workflow')
            wf_service.trg_validate(uid, 'service.quotation', new_quotation_id, 'action_draft', cr)
            quotation_obj.write({'revised_quotation_id': new_quotation_id,
                                })
            return {
                'name': "Revised Quotation",
                'view_mode': 'form,tree',
                'view_type': 'form',
                'res_model': 'service.quotation',
                'res_id': new_quotation_id,
                'type': 'ir.actions.act_window',
                'nodestroy': True,
                'target': 'current',
            }

quotation_wizard()
