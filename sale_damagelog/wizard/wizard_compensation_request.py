import netsvc
import time
from osv import osv #, fields
from tools.translate import _

class wizard_compensation_request(osv.osv_memory):
    _name = "wizard_compensation_request"
    _description = "Multiple compensation requests"
    _columns = {
                }
    
    def default_get(self, cr, uid, fields, context):
        sale_damagelog_id = context and context.get('active_ids', []) or []
        res = super(wizard_compensation_request, self).default_get(cr, uid, fields, context=context)
        res.update({'sale_damagelog_id': sale_damagelog_id or False})
        return res

    def approve_compensation(self, cr, uid, ids, context=None):
        rec_ids = context and context.get('active_ids', False)
        obj_compreq = self.pool.get('sale.comprequest')
        compreqs = obj_compreq.browse(cr, uid, rec_ids, context=context)
        state_not_draft = []
        for compreq in compreqs:
            if compreq.state != 'draft' and compreq.state != 'Draft':
                state_not_draft.append(compreq)
        #import ipdb; ipdb.set_trace()
        if state_not_draft:
            raise osv.except_osv(
                _('Some records are not drafts'),
                _('All records must be drafts for all request to be approved'))
        else:
            obj_compreq.action_confirm(cr, uid, rec_ids)
            return {
                    'type': 'ir.actions.act_window_close',
                    }


wizard_compensation_request()
