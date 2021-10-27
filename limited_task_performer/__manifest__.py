{
    'name': 'Limited task performer',
    'version': '14.0.1.0.0',
    'category': 'Project Management',
    'author': 'Simbioz',
    'website': 'simbioz.ua',
    'license': 'AGPL-3',
    'images': [
    ],
    'depends': [
        'project',
        'project_task_subtask',
        'project_wbs_impact',
        'ks_dashboard_ninja',
    ],
    'data': [
        'security/groups.xml',
        'security/ir.model.access.csv',
        'views/project_task.xml',
    ],
    'demo': [
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
