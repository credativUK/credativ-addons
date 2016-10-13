# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2016 credativ ltd (<http://www.credativ.co.uk>).
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

import sys
import traceback
import logging
from datetime import datetime

from openerp import pooler, netsvc
from openerp.osv import fields, orm
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
from openerp.tools.translate import _

from contextlib import closing
from openerp.addons.connector.queue.job import job
from openerp.addons.connector.exception import JobError
from openerp.addons.connector.session import ConnectorSession

_logger = logging.getLogger(__name__)

@job
def trusted_auto_confirm_job(session, record_id, context=None):
    purchase_obj = session.pool.get('purchase.order')
    return purchase_obj.trusted_auto_confirm(session.cr, session.uid, record_id, context=context)

class purchase_order(orm.Model):
    _inherit = 'purchase.order'

    _columns = {
            'auto_confirm_date': fields.date('Confirm On (if trusted)', help="Date on which this RFQ can be auto-confirmed if the supplier is marked as trusted.", readonly=True, states={'draft': [('readonly', False)]}),
    }

    def trusted_auto_confirm(self, cr, uid, ids, context=None):
        ids = hasattr(ids, '__iter__') and ids or [ids]
        conf_obj = self.pool.get('ir.config_parameter')
        user_obj = self.pool.get('res.users')
        mail_obj = self.pool.get('mail.mail')
        mail_from = user_obj.read(cr, uid, uid, ['email'], context=context).get('email')
        mail_to = conf_obj.get_param(cr, uid, 'purchase.trusted_confirmation_notify', context=context)
        wf_service = netsvc.LocalService("workflow")
        errors = []
        with closing(pooler.get_db(cr.dbname).cursor()) as _cr:
            old_name, new_name = 'Unknown', 'Unknown'
            for purchase_id in ids:
                try:
                    purchase = self.browse(_cr, uid, purchase_id, context=context)
                    old_name = purchase.name
                    if purchase.state != 'draft':
                        continue
                    wf_service.trg_validate(uid, 'purchase.order', purchase_id, 'purchase_confirm', _cr)
                    purchase.refresh()
                    new_name = purchase.name
                    if mail_to:
                        mail_values = {
                            'email_to': mail_to,
                            'subject': 'Trusted RFQ %s/PO %s Confirmed' % (old_name, new_name),
                            'body_html': 'Trusted RFQ %s/PO %s has been auto-confirmed.' % (old_name, new_name),
                            'state': 'outgoing',
                            'type': 'email',
                        }
                        if mail_from:
                            mail_values.update({'email_from': mail_from})
                        mail_id = mail_obj.create(_cr, uid, mail_values, context=context)
                        mail_obj.send(_cr, uid, [mail_id], context=context)
                except Exception, e:
                    _cr.rollback()
                    formatted_info = ''.join(traceback.format_exception(*(sys.exc_info())))
                    err_msg = 'Unable to auto-confirm trusted RFQ %s/PO %s.\n%s' % (old_name, new_name, formatted_info)
                    _logger.error(err_msg)
                    errors.append(err_msg)
                    continue
                _cr.commit()
        if errors:
            error_str = '\n' + '\n'.join(errors)
            raise JobError(_('Some RFQs could not be confirmed:') + error_str)

    def run_trusted_auto_confirm(self, cr, uid, context=None):
        confirm_date = datetime.now().strftime(DEFAULT_SERVER_DATE_FORMAT)
        purchase_ids = self.search(cr, uid, [('state','=','draft'),('partner_id.trusted_supplier','=',True),('auto_confirm_date', '<=', confirm_date)], context=context)
        session = ConnectorSession(cr, uid, context=context)
        for purchase_id in purchase_ids:
            trusted_auto_confirm_job.delay(session,
                                           purchase_id,
                                           context=context,
                                           description="Confirm Trusted RFQ")
        return True
