{
    'name': 'Public Holidays',
    'version': '1.0',
    'category': 'Others',
    'description': """

    """,
    'author': 'Credativ',
    'website': 'http://www.credativ.com',
    'images': [],
    'depends': ['hr_holidays'],
    'init_xml': [],
    'update_xml': ["public_holiday_view.xml", 
                   "holiday_data.xml",
                   "wizard/wiz_holiday_view.xml"
                   ],
    'demo_xml': [],
    'test': [],
    'installable': True,
    'auto_install': False,
#    'certificate': '?',
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
