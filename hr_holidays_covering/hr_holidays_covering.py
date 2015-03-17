from openerp import fields, models

class hr_holidays_covering(models.Model):
  _inherit = 'hr.holidays'
  covering_id = fields.Many2one('hr.employee', string='Covering')
