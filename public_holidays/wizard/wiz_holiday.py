from osv import osv, fields
from tools.translate import _
import time
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import calendar

class wiz_holiday(osv.osv_memory):
    _name = 'wiz.holiday'
    _description = 'Testing all the functions '
    _columns = {
        'h_date': fields.date('Date', required=True),
        'no_of_days': fields.integer('No. of Working Days'),
        'country_id': fields.many2one('res.country', 'Country'),
        'dummy_check': fields.boolean('Dummy'),
        'isWorkingDay': fields.boolean('Is Working Day'),
        'nextWorkingDay': fields.date('Next Working Date'),
        'desc': fields.text('Description'),
    }
    
    _defaults = {
         'dummy_check': False,
         'h_date': lambda *a: time.strftime('%Y-%m-%d')
    }
    
    def check_func(self, cr, uid, ids, context=None):
        holiday_obj = self.pool.get('hr.holidays')
        browse_recid = self.browse(cr, uid, ids[0])
        country = browse_recid.country_id and browse_recid.country_id.id or False
        result = holiday_obj.getWorkingDays(cr, uid, browse_recid.h_date, country, browse_recid.no_of_days, context=context)
        return self.write(cr, uid, ids, {'isWorkingDay': result['isWorkingDay'], 'nextWorkingDay': result['nextWorkingDay'], 'desc': result['desc']})

wiz_holiday()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: