import time
from datetime import datetime, timedelta
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
    _description = 'Define Rules for recurring public holidays'
    _columns = {
        'name': fields.char('Name', size=128),
        'recurring_week': fields.selection([('0','First'),('1','Second'),('2','Third'),('3','Fourth'),('-1','Last')], 'Week'),
        'recurring_day': fields.many2one('res.weekdays', 'Day'),
        'recurring_month': fields.selection([('01','January'),('02','February'),('03','March'),('04','April'),('05','May'),('06','June'),('07','July'),('08','August'),('09','September'),('10','October'),('11','November'),('12','December')], 'Month'),
        'active': fields.boolean('Active'),
        'country_ids': fields.many2many('res.country', 'country_holiday_rel', 'holiday_id', 'country_id', 'Countries'),
    }

    _defaults = {
         'active': lambda *a : 1
    }

    def _fetch_holidays(self, cr, uid, ids=False, context=None):
        print "ir cron job called"
        if not ids:
            ids = self.search(cr, uid, [])
        if context is None:
            context = {}
        for rule in self.browse(cr, uid, ids, context=context):
            #get all the holidays between now and now +1 year
            start_dt = time.strftime('%Y-%m-%d')
            date2 = datetime.strptime(start_dt, '%Y-%m-%d') + relativedelta(years=1)
            end_dt = datetime.strftime(date2, '%Y-%m-%d')
            dt_time_date = datetime.strptime(start_dt, '%Y-%m-%d')
            rec_holidays = self.pool.get('hr.public.holiday').search(cr, uid, [('actual_date','>=',start_dt),('actual_date','<=',end_dt),('rule_id','=',rule.id)])
            if not rec_holidays:
                for country in rule.country_ids:
                    year = dt_time_date.year
                    if not int(rule.recurring_month) >= dt_time_date.month:
                        year += 1
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
                    effective_date = str(year)+'-'+str(rule.recurring_month)+'-'+str(d1)
                    holiday = self.pool.get('hr.public.holiday').onchange_holidays(cr, uid, ids, effective_date, country.id, rule.id)
#                        actual_date = self.pool.get('hr.public.holiday').get_actual_holiday(cr, uid, effective_date, country.id, rule.id)
                    vals = {
                        'name': rule.name,
                        'effective_date': effective_date,
                        'actual_date': holiday['value']['actual_date'],
                        'previous_holiday': holiday['value']['previous_holiday'],
                        'next_holiday': holiday['value']['next_holiday'],
                        'rule_id': rule.id,
                        'country_id': country.id
                    }
                    self.pool.get('hr.public.holiday').create(cr, uid, vals)
                    if holiday['value']['previous_holiday']:
                        prev_id = self.pool.get('hr.public.holiday').search(cr, uid, [('actual_date','=',holiday['value']['previous_holiday']),('country_id','=',country.id)])
                        if prev_id:
                            self.pool.get('hr.public.holiday').write(cr, uid, prev_id, {'next_holiday':holiday['value']['actual_date']})
                    
                    if holiday['value']['next_holiday']:
                        next_id = self.pool.get('hr.public.holiday').search(cr, uid, [('actual_date','=',holiday['value']['previous_holiday']),('country_id','=',country.id)])
                        if next_id:
                            self.pool.get('hr.public.holiday').write(cr, uid, next_id, {'previous_holiday':holiday['value']['actual_date']})
                        
        return True
            
hr_public_holiday_rule()

class hr_public_holiday(osv.osv):
    _name = 'hr.public.holiday'
    _columns = {
        'name': fields.char('Name', size=64),
        'effective_date': fields.date('Effective Date'),
        'actual_date': fields.date('Actual Date'),
        'previous_holiday': fields.date('Previous Holiday'),
        'next_holiday': fields.date('Next Holiday'),
        'rule_id': fields.many2one('hr.public.holiday.rule', 'Holiday Rule', help="To know it was auto-generated or manually entered holiday"),
        'country_id': fields.many2one('res.country', 'Country')
    }

    def onchange_holidays(self, cr, uid, ids, effective_date, country=False, rule=False, context=None):
        if context is None:
            context = {}
        actual_date = False
        result={}
        if effective_date:
            actual_date = self.get_actual_holiday(cr, uid,  effective_date, country, rule)
            #next holiday date
            prev_date = self.search(cr, uid, [('actual_date','<',actual_date),('country_id','=',country)], order="actual_date DESC")
            next_date = self.search(cr, uid, [('actual_date','>',actual_date),('country_id','=',country)], order="actual_date ASC")
            result['value'] = {
                'actual_date': actual_date,
                'previous_holiday': prev_date and self.browse(cr, uid, prev_date[0]).actual_date or False,
                'next_holiday': next_date and self.browse(cr, uid, next_date[0]).actual_date or False,
                }
        
        return result
    
    def get_actual_holiday(self, cr, uid, actual_date, country=False, rule=False, context=None):
        if context == None:
            context={}
        srch_hol = self.search(cr, uid, [('actual_date', '=', actual_date),('country_id','=',country)])
        weekends = []
        if country:
            for country_weekend in self.pool.get('res.country').browse(cr, uid, country).weekend_ids:
                weekends.append(country_weekend.id)
        if srch_hol or (rule and self.pool.get('hr.public.holiday.rule').browse(cr, uid, rule).recurring_day.id in weekends):
             dd = datetime.strptime(actual_date, '%Y-%m-%d') + timedelta(days=1)
             actual_date = self.get_actual_holiday(cr, uid, dd, country=country, rule=rule, context=context)
        return actual_date
    
hr_public_holiday()