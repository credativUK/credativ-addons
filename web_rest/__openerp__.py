# -*- coding: utf-8 -*-
{
    'name': "web_rest",

    'summary': """Add RESTfull routes to odoo""",

    'description': """
        Add RESTfull routes to odoo
    """,

    'author': "credativ",
    'website': "http://www.credativ.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Web',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['web'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo.xml',
    ],
}
