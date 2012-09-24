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
    
    def _get_next_working_day(self, cr, uid, nxt_wrking_date, country, context=None):
        holiday_obj = self.pool.get('hr.holidays')
        nxt_wrking_date = datetime.strftime(nxt_wrking_date, '%Y-%m-%d')
        holiday = holiday_obj.search(cr, uid, [('actual_date','=',nxt_wrking_date),('country_id','=',country)])
        weekends = []
        if country:
            country_id = self.pool.get('res.country').browse(cr, uid, country)
            for country_weekend in country_id.weekend_ids:
                weekends.append(country_weekend.code)
        
        if holiday or (datetime.strptime(nxt_wrking_date, '%Y-%m-%d').isoweekday() in weekends):
            date1 = datetime.strptime(nxt_wrking_date, '%Y-%m-%d') + relativedelta(days=1)
            nxt_wrking_date = self._get_next_working_day(cr, uid, date1, country, context=context)
          
        return nxt_wrking_date
        
            
    def check_func(self, cr, uid, ids, context=None):
        holiday_obj = self.pool.get('hr.holidays')
        browse_recid = self.browse(cr, uid, ids[0])
        country = browse_recid.country_id and browse_recid.country_id.id or False
        # check if its the working day or not
        flag = True
        holidays = holiday_obj.search(cr, uid, [('actual_date','=',browse_recid.h_date),('country_id','=',country)])
        if holidays:
            flag = False
        
        # fetch the next x no. of working days
        nextWorkingDays = []
        i=1
        while(len(nextWorkingDays) < browse_recid.no_of_days):
            date1 = datetime.strptime(browse_recid.h_date, '%Y-%m-%d') + relativedelta(days=i)
            nxt_day = self._get_next_working_day(cr, uid, date1, country)
            if not nextWorkingDays.__contains__(nxt_day):
                nextWorkingDays.append(nxt_day)
            i += 1

        desc = 'Next '+ str(browse_recid.no_of_days) + ' working days : \n'
        for nextday in nextWorkingDays:
            desc += nextday + '\n'
            
        return self.write(cr, uid, ids, {'isWorkingDay': flag, 'nextWorkingDay': nextWorkingDays[0], 'desc': desc, 'dummy_check': True})

wiz_holiday()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: