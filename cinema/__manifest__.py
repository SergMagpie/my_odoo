# -*- coding: utf-8 -*-
{
    'name': "Cinema",

    'summary': """
        The best cinema manager""",

    'description': """
        Long description of module's purpose
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'mail'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/searches_and_groups.xml',
        'views/kanbans.xml',
        'views/views.xml',
        'views/templates.xml',
        'data/ir_sequence.xml',
        'views/inheriting_views.xml',
        'wizard/wizard_views.xml',
        'views/place_category.xml',
        'views/tickets_price.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
