from osv import osv, fields
from tools.translate import _
import datetime
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
         'dummy_check': False
    }
    
    def check_func(self, cr, uid, ids, context=None):
        holiday_obj = self.pool.get('hr.public.holiday')
        browse_recid = self.browse(cr, uid, ids[0])
        country = browse_recid.country_id and browse_recid.country_id.id or False
        # check if its the working day or not
        flag = True
        holidays = holiday_obj.search(cr, uid, [('actual_date','=',browse_recid.h_date),('country_id','=',country)])
        if holidays:
            flag = False
        # fetch the next working date
        nxtDays = holiday_obj.search(cr, uid, [('actual_date','>',browse_recid.h_date),('country_id','=',country)], order="actual_date ASC")
        nextWorkingDay = nxtDays and holiday_obj.browse(cr, uid, nxtDays[0]).actual_date or False
        
        # fetch the next x no. of working days
        no_of_days = browse_recid.no_of_days
        desc = 'Next '+ str(no_of_days) + ' working days : \n'
        for nextday in holiday_obj.browse(cr, uid, nxtDays):
            if no_of_days != 0:
                desc += nextday.actual_date + '\n'
                no_of_days -= 1
        return self.write(cr, uid, ids, {'isWorkingDay': flag, 'nextWorkingDay': nextWorkingDay, 'desc': desc, 'dummy_check': True})
    
wiz_holiday()