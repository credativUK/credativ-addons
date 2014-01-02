from osv import osv, fields
from tools.translate import _

import time

class hr_analytic_timesheet(osv.osv):
    _name = 'hr.analytic.timesheet'
    _inherit = 'hr.analytic.timesheet'

    _columns = {
        'dummy_field' : fields.char("", 1),
    }


    def replicate_line(self, cr, uid, ids, context=None):
        line_id = self.browse(cr, uid, ids[0]).line_id.id
        context['line_id'] = line_id
        context['tsht_id'] = ids[0]

        wiz_obj  = self.pool.get('hr.timesheet.line.replicate.wizard')
        self_obj = self.pool.get('hr.analytic.timesheet')

        self_read = self_obj.read(cr, uid, ids[0], context=context)

        if not self_read['date']:
            raise except_osv(
                                _('Line has no date set.'),
                                _('Cannot replicate on a date-basis if there is no base date specified.')
                            )

        wiz_id  = wiz_obj.create(cr, uid, {}, context=context)
        wiz_obj.write(cr, uid, wiz_id, {'start_date' : self_read['date']})

        return {'type'      : 'ir.actions.act_window'             ,
                'name'      : 'Timesheet Line Duplicator'         ,
                'res_model' : 'hr.timesheet.line.replicate.wizard',
                'res_id'    : wiz_id                              ,  
                'view_type' : 'form'                              ,
                'view_mode' : 'form'                              ,
                'view_id'   : False                               ,
                'target'    : 'new'                               ,
                'context'   : context                             ,
                'nodestroy' : True                                ,
                'domain'    : '[]'                                ,
        }


hr_analytic_timesheet()
