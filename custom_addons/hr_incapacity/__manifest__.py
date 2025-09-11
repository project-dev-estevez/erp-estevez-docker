{
    'name': 'Incapacidades Estevez',
    'version': '1.0',
    'category': 'Human Resources',
    'summary': 'Gestión de incapacidades para empleados',
    'description': """
        Módulo para gestionar incapacidades de empleados
    """,
    'author': 'Estevez.Jor',
    'depends': ['hr', 'hr_holidays'],
    'data': [
        'views/hr_incapacity_views.xml',
        'views/hr_employee_views.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}