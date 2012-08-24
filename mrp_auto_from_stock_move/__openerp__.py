# -*- coding: utf-8 -*-
{
    "name" : "Delivery Driven Automatic Manufacturing",
    "version" : "1.1",
    "author" : "credativ",
    "website" : "http://www.credativ.com",
    "category" : "Manufacturing",
    "sequence": 18,
    "images" : [],
    "depends" : ["mrp"],
    "description": """
This is the base module to manage the manufacturing process in OpenERP.
=======================================================================

Features:
---------
    As soon as an outgoing raw materials shipment to the subcontractor is completed, 
    the corresponding incoming shipment of the Finished Products will be visible and 
    available in the Incoming Shipments screen.
    """,
    'init_xml': [],
    'update_xml': [
        'mrp_workflow.xml',
        'mrp_view.xml',
    ],
    'demo_xml': [],
    'test': [],
    'installable': True,
    'active': False,
    'certificate': '',
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
