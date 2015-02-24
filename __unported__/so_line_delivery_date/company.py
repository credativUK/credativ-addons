from openerp.osv import fields, osv

class res_company(osv.osv):
    _inherit = 'res.company'
    _columns = {
            'delivery_date_per_line' : fields.boolean(string='Delivery dates are per-line.', help='This specifies the relationship between Sale Orders and delivery dates.'), 
    }

    _defaults = {
            'delivery_date_per_line' : True,
    }

res_company()
