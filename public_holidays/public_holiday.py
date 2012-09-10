import time
from datetime import datetime
from dateutil.relativedelta import relativedelta
import calendar

from osv import fields, osv
from tools.translate import _

class res_weekdays(osv.osv):
    _name = 'res.weekdays'
    _columns = {
        'name': fields.selection([('Monday','Monday'),('Tuesday','Tuesday'),('Wednesday','Wednesday'),('Thursday','Thursday'),('Friday','Friday'),('Saturday','Saturday'),('Sunday','Sunday')], 'Day'),
    }
    
res_weekdays()

class res_country(osv.osv):
    _inherit = 'res.country'
    _columns = {
        'weekend_ids': fields.many2many('res.weekdays', 'rel_weekdays_country', 'country_id', 'week_id', 'Weekends'),
    }
    
res_country()

class hr_public_holiday_rule(osv.osv):
    _name = 'hr.public.holiday.rule'
    _columns = {
        'name': fields.char('Name', size=128),
        'holiday_date': fields.date('Date'),
        'is_recurring': fields.boolean('Recurring'),
        'recurring_week': fields.selection([('0','First'),('1','Second'),('2','Third'),('3','Fourth'),('-1','Last')], 'Week'),
        'recurring_day': fields.many2one('res.weekdays', 'Day'),
#        'recurring_day': fields.selection([('MONDAY','Monday'),('TUESDAY','Tuesday'),('WEDNESDAY','Wednesday'),('THURSDAY','Thursday'),('FRIDAY','Friday'),('SATURDAY','Saturday'),('SUNDAY','Sunday')], 'Day'),
        'recurring_month': fields.selection([('01','January'),('02','February'),('03','March'),('04','April'),('05','May'),('06','June'),('07','July'),('08','August'),('09','September'),('10','October'),('11','November'),('12','December')], 'Month'),
        'active': fields.boolean('Active'),
        'country_ids': fields.many2many('res.country', 'country_holiday_rel', 'holiday_id', 'country_id', 'Countries'),
    }

    _defaults = {
         'active': lambda *a : 1
    }

    def check_weekend(self, cr, uid, rule, date1, country, weekend):
        actual_date = date1
        if rule.recurring_day.id == weekend:
             dd = datetime.strptime(start_dt, '%Y-%m-%d') + datetime.timedelta(days=1)
             actual_date = self.check_weekend(cr, uid, rule, dd)
        srch_hol = self.pool.get('hr.public.holiday').search(cr, uid, [('actual_date', '=', actual_date),('country_id','=',country)])
        if srch_hol:
            actual_date = self.check_weekend(cr, uid, rule, actual_date, country, weekend)
        return actual_date
                
    def _fetch_holidays(self, cr, uid, ids=False, context=None):
        print "ir cron job called"
        if not ids:
            ids = self.search(cr, uid, [])
        return self._fetch_holiday(cr, uid, ids, context=context)

    def _fetch_holiday(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        for rule in self.browse(cr, uid, ids, context=context):
            #get all the holidays between now and now +1 year
            start_dt = time.strftime('%Y-%m-%d')
            date2 = datetime.strptime(start_dt, '%Y-%m-%d') + relativedelta(years=1)
            end_dt = datetime.strftime(date2, '%Y-%m-%d')
            print "ssssssssssss",start_dt, end_dt
            dt_time_date = datetime.strptime(start_dt, '%Y-%m-%d')
            rec_holidays = self.pool.get('hr.public.holiday').search(cr, uid, [('actual_date','>=',start_dt),('actual_date','<=',end_dt),('rule_id','=',rule.id)])
            if not rec_holidays:
                if rule.is_recurring:
                    for country in rule.country_ids:
                        for country_weekend in country.weekend_ids:
                            year = dt_time_date.year
                            if not int(rule.recurring_month) >= dt_time_date.month:
                                year += 1
                            print year 
                            c = calendar.monthcalendar(int(year), int(rule.recurring_month))
                            if rule.recurring_day.name == 'Monday':
                                cc = calendar.MONDAY
                            elif rule.recurring_day.name == 'Tuesday':
                                cc = calendar.TUESDAY
                            elif rule.recurring_day.name == 'Wednesday':
                                cc = calendar.WEDNESDAY
                            elif rule.recurring_day.name == 'Thursday':
                                cc = calendar.THURSDAY
                            elif rule.recurring_day.name == 'Friday':
                                cc = calendar.FRIDAY
                            elif rule.recurring_day.name == 'Saturday':
                                cc = calendar.SATURDAY
                            elif rule.recurring_day.name == 'Sunday':
                                cc = calendar.SUNDAY
                            d1 = c[int(rule.recurring_week)][cc]
                            #to skip the weeks with 0 dates
                            if d1 == 0:
                                if rule.recurring_week == -1:
                                    d1 = c[int(rule.recurring_week)-1][cc]
                                else:
                                    d1 = c[int(rule.recurring_week)+1][cc]
                            if d1 < 10:
                                d1 = '0'+str(d1)
                            date1 = str(year)+'-'+str(rule.recurring_month)+'-'+str(d1)
                            actual_date = self.check_weekend(cr, uid, rule,date1, country.id, country_weekend.id)
                            vals = {
                                'effective_date': date1,
                                'actual_date': actual_date,
                                'previous_holiday': False,
                                'next_holiday': False,
                                'rule_id': rule.id,
                                'country_id': country.id
                            }
                            self.pool.get('hr.public.holiday').create(cr, uid, vals)

        return True
            
hr_public_holiday_rule()

class hr_public_holiday(osv.osv):
    _name = 'hr.public.holiday'
    _rec_name = 'effective_date'
    _columns = {
        'effective_date': fields.date('Effective Date'),
        'actual_date': fields.date('Actual Date'),
        'previous_holiday': fields.date('Previous Holiday'),
        'next_holiday': fields.date('Next Holiday'),
        'rule_id': fields.many2one('hr.public.holiday.rule', 'Holiday Rule', help="To know it was auto-generated or manually entered holiday"),
        'country_id': fields.many2one('res.country', 'Country')
    }
    
hr_public_holiday()