
from osv import fields, osv

class hr_holidays_covering(osv.osv):
  _inherit = 'hr.holidays'
  _columns = {
    'covering_id' : fields.many2one('hr.employee', 'Covering'),
  }

hr_holidays_covering()
