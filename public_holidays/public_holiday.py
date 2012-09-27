import time
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import calendar

from osv import fields, osv
from tools.translate import _

class res_weekdays(osv.osv):
    _name = 'res.weekdays'
    _columns = {
        'code': fields.integer('Code'),
        'name': fields.selection([('Monday','Monday'),('Tuesday','Tuesday'),('Wednesday','Wednesday'),('Thursday','Thursday'),('Friday','Friday'),('Saturday','Saturday'),('Sunday','Sunday')], 'Day'),
    }
    
res_weekdays()

class res_country(osv.osv):
    _inherit = 'res.country'
    _columns = {
        'allow_substitute': fields.boolean('Allow Substitute Holidays'),
        'weekend_ids': fields.many2many('res.weekdays', 'rel_weekdays_country', 'country_id', 'week_id', 'Weekends'),
    }
    _defaults = {
         'allow_substitute': False
    }
res_country()

class hr_holiday_rule(osv.osv):
    _name = 'hr.holiday.rule'
    _description = 'Define Rules for recurring public holidays'
    _columns = {
        'name': fields.char('Name', size=128),
        'week': fields.selection([('0','First'),('1','Second'),('2','Third'),('3','Fourth'),('-1','Last')], 'Week'),
        'day': fields.many2one('res.weekdays', 'Day of Week'),
        'month': fields.selection([('01','January'),('02','February'),('03','March'),('04','April'),('05','May'),('06','June'),('07','July'),('08','August'),('09','September'),('10','October'),('11','November'),('12','December')], 'Month'),
        'day1': fields.selection([('01','1st of the month'),('02','2nd of the month'),('03','3rd of the month'),('04','4th of the month'),('05','5th of the month'),('06','6th of the month'),('07','7th of the month'),('08','8th of the month'),('09','9th of the month'),('10','10th of the month'),('11','11th of the month'),('12','12th of the month'),('13','13th of the month'),('14','14th of the month'),('15','15th of the month'),
                                  ('16','16th of the month'),('17','17th of the month'),('18','18th of the month'),('19','19th of the month'),('20','20th of the month'),('21','21st of the month'),('22','22nd of the month'),('23','23th of the month'),('24','24th of the month'),('25','25th of the month'),('26','26th of the month'),('27','27th of the month'),('28','28th of the month'),('29','29th of the month'),('30','30th of the month'),('31','31st of the month')], 'Day of Month'),
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
            for country in rule.country_ids:
                year = dt_time_date.year
                if rule.month and rule.day:
                    if not int(rule.month) >= dt_time_date.month:
                        year += 1
                    c = calendar.monthcalendar(int(year), int(rule.month))
                    if rule.day.name == 'Monday':
                        cc = calendar.MONDAY
                    elif rule.day.name == 'Tuesday':
                        cc = calendar.TUESDAY
                    elif rule.day.name == 'Wednesday':
                        cc = calendar.WEDNESDAY
                    elif rule.day.name == 'Thursday':
                        cc = calendar.THURSDAY
                    elif rule.day.name == 'Friday':
                        cc = calendar.FRIDAY
                    elif rule.day.name == 'Saturday':
                        cc = calendar.SATURDAY
                    elif rule.day.name == 'Sunday':
                        cc = calendar.SUNDAY
                    d1 = c[int(rule.week)][cc]
                    #to skip the weeks with 0 dates
                    if d1 == 0:
                        if rule.week == -1:
                            d1 = c[int(rule.week)-1][cc]
                        else:
                            d1 = c[int(rule.week)+1][cc]
                    if d1 < 10:
                        d1 = '0'+str(d1)
                    effective_date = str(year)+'-'+str(rule.month)+'-'+str(d1)
                elif rule.day1:
                    effective_date = str(year)+'-'+str(rule.month)+'-'+str(rule.day1)
                else:
                    raise osv.except_osv(
                    _('Error !'),
                    _('Either select a week and day of week for a particular month or select day of month.'))
                try:
                    date1 = time.strptime(effective_date, '%Y-%m-%d')
                except ValueError:
                    print('Invalid date!'), effective_date
                    break   
                if not (effective_date >= start_dt and effective_date <= end_dt):
                    effective_date = datetime.strptime(effective_date, '%Y-%m-%d') + relativedelta(years=1)
                    effective_date = datetime.strftime(effective_date, '%Y-%m-%d')
                effective_date = datetime.strftime(datetime.strptime(effective_date, '%Y-%m-%d'),  '%Y-%m-%d %H:%M:%S')
                holiday = self.pool.get('hr.holidays').onchange_holidays(cr, uid, ids, effective_date, country.id, rule.id)
                hol_ids = self.pool.get('hr.holidays').search(cr, uid, [('date_from','=',effective_date),('country_id','=',country.id),('name','=',rule.name)])
                if not hol_ids:
                    vals = {
                        'name': rule.name,
                        'holiday_type': 'employee',
#                        'category_id': self.pool.get('hr.employee.category').search(cr, uid, [('name','=','Ranking')]) and self.pool.get('hr.employee.category').search(cr, uid, [('name','=','Ranking')])[0] or False, 
                        'holiday_status_id': self.pool.get('hr.holidays.status').search(cr, uid, [('name','=', 'Legal Leaves')]) and self.pool.get('hr.holidays.status').search(cr, uid, [('name','=', 'Legal Leaves')])[0] or False,
                        'date_from': effective_date,
                        'date_to': holiday['value']['date_to'],
                        'number_of_days_temp':holiday['value']['number_of_days_temp'],
                        'actual_date': holiday['value']['actual_date'],
                        'previous_holiday': holiday['value']['previous_holiday'],
                        'next_holiday': holiday['value']['next_holiday'],
                        'rule_id': rule.id,
                        'country_id': country.id,
                        'is_recurring': True
                    }
                    self.pool.get('hr.holidays').create(cr, uid, vals)
                    
        return True
    
    def create(self, cr, uid, vals, context=None):
        res = super(hr_holiday_rule, self).create(cr, uid, vals, context=context)
        cron_id = self.pool.get('ir.cron').search(cr, uid, [('function', 'ilike', '_fetch_holidays'),('model', '=', 'hr.holiday.rule')])
        if cron_id:
            try:
                next = (datetime.now() + relativedelta(minutes=1)).strftime('%Y-%m-%d %H:%M:%S')
                cr.execute('UPDATE ir_cron set nextcall = \'%s\' where numbercall <> 0 and active and id= %s '  % (next, int(cron_id[0])))
            finally:
                cr.commit()
        
        print "---create called---"
        return res
            
hr_holiday_rule()

class hr_holidays(osv.osv):
    _inherit = 'hr.holidays'
    _order = 'actual_date asc'
    
    _columns = {
        'actual_date': fields.date('Actual Date', help="Actual Date on which the holiday falls"),
        'previous_holiday': fields.date('Previous Holiday'),
        'next_holiday': fields.date('Next Holiday'),
        'rule_id': fields.many2one('hr.holiday.rule', 'Holiday Rule', help="To know it was auto-generated or manually entered holiday"),
        'country_id': fields.many2one('res.country', 'Country'),
        'is_recurring': fields.boolean('Recurring Holiday'),
    }
    
    _defaults = {
        'is_recurring': False,
    }

    def onchange_holidays(self, cr, uid, ids, effective_date, country=False, rule=False, context=None):
        if context is None:
            context = {}
        actual_date = False
        result={}
        if effective_date:
            actual_date = self.get_actual_holiday(cr, uid,  effective_date, country, rule)
            if type(actual_date) == datetime:
                actual_date = datetime.strftime(actual_date, '%Y-%m-%d')
            result['value'] = {
                'date_to': effective_date,
                'number_of_days_temp': self.onchange_date_from(cr, uid, ids, effective_date, effective_date)['value']['number_of_days_temp'],
                'actual_date': actual_date,
                'previous_holiday': self._get_prev_date(cr, uid, actual_date, country),
                'next_holiday': self._get_next_date(cr, uid, actual_date, country),
                }
        return result
    
    def get_actual_holiday(self, cr, uid, actual_date, country=False, rule=False, context=None):
        if context == None:
            context={}
        srch_hol = self.search(cr, uid, [('actual_date', '=', actual_date),('country_id','=',country)])
        weekends = []
        if country:
            country_id = self.pool.get('res.country').browse(cr, uid, country)
            for country_weekend in country_id.weekend_ids:
                weekends.append(country_weekend.code)
            if country_id.allow_substitute == True:
                if type(actual_date) != datetime:
                    try:
                        actual_date = datetime.strptime(actual_date, '%Y-%m-%d')
                    except ValueError, v:
                        if len(v.args) > 0 and v.args[0][:26] == 'unconverted data remains: ':
                            actual_date = actual_date.split(" ")[0]
                            actual_date = datetime.strptime(actual_date, '%Y-%m-%d')
                        else:
                            raise v
                if (rule and actual_date.isoweekday() in weekends) or srch_hol:
                    actual_date += relativedelta(days=1)
                    dd = datetime.strftime(actual_date, '%Y-%m-%d %H:%M:%S')
                    actual_date = self.get_actual_holiday(cr, uid, dd, country=country, rule=rule, context=context)
        return actual_date
    
    def _get_prev_date(self, cr, uid, actual_date, country, context=None):
        prev_date = self.search(cr, uid, [('actual_date','<',actual_date),('country_id','=',country)], order="actual_date DESC")
        return prev_date and self.read(cr, uid, prev_date[0])['actual_date'] or False

    def _get_next_date(self, cr, uid, actual_date, country, context=None):
        next_date = self.search(cr, uid, [('actual_date','>',actual_date),('country_id','=',country)], order="actual_date ASC")
        return next_date and self.read(cr, uid, next_date[0])['actual_date'] or False
    
    def update_prev_nxt_holiday(self, cr, uid, holidays, context=None):
        for t in self.browse(cr, uid, holidays, context=context):
            prev_holiday = self._get_prev_date(cr, uid, t.actual_date, t.country_id and t.country_id.id or False)
            next_holiday = self._get_next_date(cr, uid, t.actual_date, t.country_id and t.country_id.id or False)
            osv.osv.write(self, cr, uid, [t.id], {'previous_holiday':prev_holiday, 'next_holiday':next_holiday})
        return True
            
    def create(self, cr, uid, vals, context=None):
        res = super(hr_holidays, self).create(cr, uid, vals, context=context)
        holidays = self.search(cr, uid, [('is_recurring','=',True)], context=context)
        self.update_prev_nxt_holiday(cr, uid, holidays, context=context)
        return res
    
    def write(self, cr, uid, ids, vals, context=None):
        res = super(hr_holidays, self).write(cr, uid, ids, vals, context=context)
        holidays = self.search(cr, uid, [('is_recurring','=',True)], context=context)
        self.update_prev_nxt_holiday(cr, uid, holidays, context=context)
        return res
    
    def unlink(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        res = super(hr_holidays, self).unlink(cr, uid, ids, context=context)
        holidays = self.search(cr, uid, [('id','not in',ids),('is_recurring','=',True)], context=context)
        self.update_prev_nxt_holiday(cr, uid, holidays, context=context)
        return res
    
hr_holidays()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: