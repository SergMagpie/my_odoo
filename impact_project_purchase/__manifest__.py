# -*- coding: utf-8 -*-
{
    'name': "Impact project purchase",

    'summary': """
        Creates the relationship of procurement processes with the project""",

    'author': "Sibmioz, Sasha Kochyn",
    'maintainer': 'Simbioz Holding',
    'website': 'https://simbioz.ua',
    'category': '',
    'version': '14.0.1.0.0',
    'license': 'LGPL-3',
    'depends': [
        'project',
        'purchase',
        'stock',
        'purchase_stock',
        'account',
        'purchase_request',
        'impact_project_stock',
    ],

    'data': [
        'views/purchase_order.xml',
        'views/project.xml',
        'views/project_relatives.xml',
        'views/purchase_order_line.xml',
        'views/purchase_request.xml',
        'views/purchase_request_line.xml',
        'wizard/purchase_request_line_make_purchase_order_view.xml',
    ],
    'demo': [],
    'qweb': [],
    'installable': True,
    'application': False,
    'auto_install': False,
}
