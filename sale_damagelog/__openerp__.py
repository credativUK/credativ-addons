# -*- encoding: utf-8 -*-
{
    'name': 'Sale Damage Log',
    'version': '1.0',
    'category': 'Generic Modules/Sales & Purchases',
    'description': """This Module allows you to manage the log for damaged products.""",
    'author': 'Credativ',
    'depends': ['sale','crm','crm_claim'],
    'init_xml': [],
    'update_xml': [
        'security/ir.model.access.csv',
        'sale_damagelog_view.xml',
        'sale_comprequest_view.xml',
        'sale_comprequest_sequence.xml',
        'wizard/create_damagelog.xml'
    ],
    'demo_xml': [],
    'installable': True,
    'active': False,
    'certificate': '',
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
