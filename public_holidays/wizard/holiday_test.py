from osv import osv, fields
from tools.translate import _
import datetime
import calendar

class holiday_test(osv.osv_memory):
    _name = 'holiday.test'
    _description = 'Testing all the functions '
    _columns = {
        'h_date': fields.date('Date'),
        'isWorkingDay': fields.boolean('Is Working Day'),
        'nextWorkingDay': fields.date('Next Working Date'),
    }
    
    def isWorkingDay(self, cr, uid, ids, context=None):
        new_date = self.browse(cr, uid, ids[0]).h_date
        dt_time_date = datetime.datetime.strptime(new_date, '%Y-%m-%d')
        year = dt_time_date.year
        flag = False
        #check if its a weekday
        if dt_time_date.weekday() in range(0,5):
            #check if its a bank holiday
            rec1 = self.pool.get('hr.public.holiday').search(cr, uid, [('holiday_date','=',new_date)])
            if not rec1:
                #check if its a recurring holiday
                recs = self.pool.get('hr.public.holiday').search(cr, uid, [('is_recurring','=',True)])
                if recs:
                    for r in self.pool.get('hr.public.holiday').browse(cr, uid, recs):
                        c = calendar.monthcalendar(int(year), int(r.recurring_month))
                        print "cccccccc", c
                        if r.recurring_day == 'MONDAY':
                            cc = calendar.MONDAY
                        elif r.recurring_day == 'TUESDAY':
                            cc = calendar.TUESDAY
                        elif r.recurring_day == 'WEDNESDAY':
                            cc = calendar.WEDNESDAY
                        elif r.recurring_day == 'THURSDAY':
                            cc = calendar.THURSDAY
                        elif r.recurring_day == 'FRIDAY':
                            cc = calendar.FRIDAY
                        elif r.recurring_day == 'SATURDAY':
                            cc = calendar.SATURDAY
                        elif r.recurring_day == 'SUNDAY':
                            cc = calendar.SUNDAY
            
                        d1 = c[int(r.recurring_week)][cc]
                        #to skip the weeks with 0 dates
                        if d1 == 0:
                            if r.recurring_week == -1:
                                d1 = c[int(r.recurring_week)-1][cc]
                            else:
                                d1 = c[int(r.recurring_week)+1][cc]
                        if d1 < 10:
                            d1 = '0'+str(d1)
                        date1 = str(year)+'-'+str(r.recurring_month)+'-'+str(d1)
                        print "--------------------", date1, type(date1)
                        print new_date, type(new_date)
                        if new_date == date1:
                            print "Its a holiday !!!"
                            flag = False
                            break
                        else:
                            print "Oh! Didn't get any holiday"
                            flag = True
        
        return self.write(cr, uid, ids, {'isWorkingDay': flag})
    
    def nextWorkingDay(self, cr, uid, ids, context=None):
        self.isWorkingDay(cr, uid, ids, context=context)
        holiday_id = self.browse(cr, uid, ids[0])
        isWorkingDay = holiday_id.isWorkingDay
        nextWorkingDate = holiday_id.h_date
#        if isWorkingDay == False:
            
            
            
        return self.write(cr, uid, ids, {'nextWorkingDay': nextWorkingDate})
        
holiday_test()