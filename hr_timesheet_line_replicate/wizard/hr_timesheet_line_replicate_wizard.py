from osv import osv, fields
from osv.osv import except_osv
from tools.translate import _

import time
from datetime import datetime, timedelta

class hr_timesheet_line_replicate(osv.osv_memory):
    _name = 'hr.timesheet.line.replicate.wizard'

    _columns = {
        'start_date' : fields.date('Start Date', readonly=True),
        'end_date'   : fields.date('End Date'),
        'mon'        : fields.boolean('Monday'   ),
        'tue'        : fields.boolean('Tuesday'  ),
        'wed'        : fields.boolean('Wednesday'),
        'thu'        : fields.boolean('Thursday' ),
        'fri'        : fields.boolean('Friday'   ),
        'sat'        : fields.boolean('Saturday' ),
        'sun'        : fields.boolean('Sunday'   ),
        'except'     : fields.char('Exceptions', 1024, readonly=True),
        'new_except' : fields.date('Add Exception'),
    }

    _defaults = {
        'mon'    : True ,
        'tue'    : True ,
        'wed'    : True ,
        'thu'    : True ,
        'fri'    : True ,
        'sat'    : False,
        'sun'    : False,

        'except' : "",
    }


    def end_date_set(self, cr, uid, ids, end_str, context=None):
        self_obj = self.pool.get('hr.timesheet.line.replicate.wizard')
        self_read = self_obj.read(cr, uid, ids[0], ['new_except', 'except', 'start_date', 'end_date'], context=context)

        start_str = self_read.get('start_date', False)
        start_date  = time.strptime(start_str , '%Y-%m-%d')

        if end_str:
            end_date = time.strptime(end_str, '%Y-%m-%d')
            try:
                assert end_date > start_date
            except AssertionError:
                raise except_osv(
                                    _('Invalid end date.'),
                                    _('End date must be later than start date.')
                                )
        return []


    def add_exception(self, cr, uid, ids, context=None):
        self_obj = self.pool.get('hr.timesheet.line.replicate.wizard')
        self_read = self_obj.read(cr, uid, ids[0], ['new_except', 'except', 'start_date', 'end_date'], context=context)

        new_except = self_read.get('new_except', False)
        start_str  = self_read.get('start_date', False)
        end_str    = self_read.get('end_date', False)

        if not new_except:
            raise except_osv(  _('No date given for new exception.'),
                               _('Please supply a date you wish to exclude from this replication.')
                            )
            return []

        except_date = time.strptime(new_except, '%Y-%m-%d')
        start_date  = time.strptime(start_str , '%Y-%m-%d')
        end_date = end_str is not False and time.strptime(end_str, '%Y-%m-%d')

        try:
            assert except_date >= start_date
            if end_date:
                assert except_date <= end_date
        except AssertionError:
            raise except_osv(
                                _('Exception date does not fall within defined period.'),
                                _('Please update end date or exception date as appropriate.')
                            )
            return []

        exceptions = self_read.get('except', False)
        if not exceptions:
            exceptions = ''

        if len(exceptions) > 0:
            new_except = '\t' + new_except

        exceptions += new_except
        self_obj.write(cr, uid, ids[0], {'except' : exceptions, 'new_except' : False})
        return []


    def go(self, cr, uid, ids, context=None):
        line_id = context.get('line_id', False)
        tsht_id = context.get('tsht_id', False)

        if not (line_id and tsht_id):
            return []

        self_obj = self.pool.get('hr.timesheet.line.replicate.wizard')
        tsht_obj = self.pool.get('hr.analytic.timesheet')

        self_read = self_obj.read(cr, uid, ids[0], [], context=context)
        tsht_read = tsht_obj.read(cr, uid, tsht_id, context=context)

        start_str      = self_read.get('start_date', False)
        end_str        = self_read.get('end_date', False)
        exceptions_str = self_read.get('except', False)

        skip = {}
        skip['mon'] = not self_read.get('mon', False)
        skip['tue'] = not self_read.get('tue', False)
        skip['wed'] = not self_read.get('wed', False)
        skip['thu'] = not self_read.get('thu', False)
        skip['fri'] = not self_read.get('fri', False)
        skip['sat'] = not self_read.get('sat', False)
        skip['sun'] = not self_read.get('sun', False)

        if exceptions_str is False:
            exceptions_str = ''

        exceptions = exceptions_str.split('\t')

        start_date  = datetime.strptime(start_str , '%Y-%m-%d')
        end_date = end_str is not False and datetime.strptime(end_str, '%Y-%m-%d')

        try:
            assert end_date
        except AssertionError:
            raise except_osv(
                                _('No end-date has been specified.'),
                                _('Please specify an end date to replicate the entry until.'),
                            )
            return []
        try:
            assert end_date > start_date
        except AssertionError:
            raise except_osv(
                                _('End date must be later than start date.'),
                                _('Please specify an end date after the start date.'),
                            )
            return []

        # Replicate timesheets, skipping unchecked days and exceptions until end date.
        # End date considered to be inclusive. Could be configureable with a check-box?
        while start_date < end_date:
            start_date += timedelta(days=1)

            wday = start_date.weekday()
            if wday == 0 and skip['mon']:
                continue
            if wday == 1 and skip['tue']:
                continue
            if wday == 2 and skip['wed']:
                continue
            if wday == 3 and skip['thu']:
                continue
            if wday == 4 and skip['fri']:
                continue
            if wday == 5 and skip['sat']:
                continue
            if wday == 6 and skip['sun']:
                continue

            if start_date.strftime('%Y-%m-%d') in exceptions:
                continue

            tsht_obj.copy(cr, uid, tsht_id, {'date' : start_date.strftime('%Y-%m-%d')}, context=context)
        
        return {'type' : 'ir.actions.act_window_close'}


hr_timesheet_line_replicate()
