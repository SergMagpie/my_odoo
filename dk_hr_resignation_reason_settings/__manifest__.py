{
    'name': 'DK HR resignation reason settings',
    'summary': """DK HR resignation reason settings""",
    'category': 'Human Resources/Employees',
    'author': 'Simbioz',
    'maintainer': 'Simbioz Holding',
    'website': 'https://simbioz.ua',
    'version': '14.0.1.0.1',
    'license': 'LGPL-3',
    'depends': [
        'hr_resignation',
    ],
    'images': [],
    'data': [
        'security/ir.model.access.csv',
        'views/resignation_reason_settings.xml',
        'views/hr_resignation.xml',
    ],
    'demo': [],
    'qweb': [],
    'installable': True,
    'application': False,
    'auto_install': False,
}