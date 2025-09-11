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
        'security/hr_incapacity_security.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}