{
    'name': 'Custom Training Extension',
    'version': '1.0',
    'summary': 'Extensión para reportes de cursos y empleados',
    'description': 'Módulo que agrega catálogos y relación empleado-curso para reportes detallados.',
    'author': 'Ruth Rivera',
    'depends': ['base', 'hr', 'website_slides'],
    'data': [
        'security/ir.model.access.csv',        
        'views/hr_state_views.xml',
        'views/hr_municipality_views.xml',
        'views/hr_occupation_views.xml',
        'views/hr_employee_course_views.xml',
        'views/hr_courses_views.xml',
        'views/hr_thematics_views.xml',
        'views/menus.xml'
    ],
    'installable': True,
    'application': True,
}
