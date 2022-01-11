{
    'name': 'Shipment & Invoice status in SO',
    'summary': """ """,
    'description': """ """,
    'category': 'Sales',
    'author': 'Mykyta Maistrenko',
    'website': 'https://simbioz.ua',
    'version': '11.0.0.5',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'sale_management',
        'account',
        'stock',
    ],
    'data': [
        'views/sale_order.xml'
    ],
    'sequence': 0,
    'installable': True,
    'application': False,
    'auto_install': False,
}