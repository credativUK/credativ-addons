from osv import osv
from tools.translate import _

class wizard_compensation_request(osv.osv_memory):
    _name = "wizard_compensation_request"
    _description = "Multiple compensation request confirmation"
    _columns = {}
    
    def confirm_compensation(self, cr, uid, ids, context=None):
        rec_ids = context and context.get('active_ids', False)
        obj_compreq = self.pool.get('sale.comprequest')
        compreqs = obj_compreq.browse(cr, uid, rec_ids, context=context)
        state_not_draft = [compreq for compreq in compreqs if compreq.state != 'draft']
        if state_not_draft:
            raise osv.except_osv(
                _('User Error'),
                _('All compensations requests must be in state draft for requests to be approved'))
        else:
            obj_compreq.action_confirm(cr, uid, rec_ids)
            return {'type': 'ir.actions.act_window_close',}

wizard_compensation_request()
