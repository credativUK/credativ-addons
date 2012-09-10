import datetime
import calendar
import time

class test():
    def isWorkingDay(self, new_date, country=None):
        year = datetime.datetime.strptime(new_date, '%Y-%m-%d').year
        recs = self.pool.get('hr.public.holidays').search(cr, uid, [('is_recurring','=',True)])
        if recs:
            for r in self.pool.get('hr.public.holidays').browse(cr, uid, recs):
                c = calendar.monthcalendar(year, r.recurring_month)
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
                date1 = str(year)+'-'+str(r.recurring_month)+'-'+str(d1)
    
                if new_date == date1:
                    print "Its a holiday !!!"
                else:
                    print "Didn\'t get a holiday !!!"
    
        return True

    isWorkingDay(time.strftime('%Y-%m-%d'))
test()