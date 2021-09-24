# -*- coding: utf-8 -*-
{
    'name': "Purchase Order Import wizard",
    'summary': """This module allows you to update Purchase Order line from csv file""",
    'category': 'Purchase Management',
    'version': '14.0.1.0.2',
    'author': "Simbioz, Sasha Kochyn",
    'maintainer': 'Simbioz Holding',
    'website': 'http://simbioz.ua',
    'depends': [
        'account',
        'purchase',
        'product_barcode',
    ],
    'data': [
        'security/ir.model.access.csv',
        'wizard/purchase_order_import_wizard.xml',
        'views/purchase_order.xml',
    ],
    'qweb': [],
    'external_dependencies': {
        'python': ['pandas', ],
    },
    'application': False,
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
