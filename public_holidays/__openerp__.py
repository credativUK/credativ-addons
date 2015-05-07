{
    'name': 'Public Holidays',
    'version': '1.0',
    'category': 'Others',
    'description': """

    """,
    'author': 'credativ',
    'website': 'http://www.credativ.co.uk',
    'images': [],
    'depends': ['hr_holidays'],
    'init_xml': [],
    'update_xml': [
                   "security/ir.model.access.csv",
                   "public_holiday_view.xml", 
                   "holiday_data.xml",
                   ],
    'demo_xml': [],
    'test': [],
    'installable': True,
    'auto_install': False,
#    'certificate': '?',
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
