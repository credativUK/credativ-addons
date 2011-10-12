# -*- encoding: utf-8 -*-
{
    'name': 'Sale Damage Log',
    'version': '1.0',
    'category': 'Generic Modules/Sales & Purchases',
    'description': """This Module allows you to manage the log for damaged products.""",
    'author': 'Credativ',
    'depends': ['sale','crm_configuration'],
    'init_xml': [],
    'update_xml': [
        'sale_damagelog_view.xml'
    ],
    'demo_xml': [],
    'installable': True,
    'active': False,
    'certificate': '',
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
