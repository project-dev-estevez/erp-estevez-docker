{
    'name': "Integración HR - eLearning",
    'summary': "Integración entre módulo de empleados y cursos eLearning",
    'description': """
        Módulo que muestra los cursos inscritos por cada empleado en su ficha de RRHH
    """,
    'author': "Estevez.Jor",
    'website': "https://estevez-erp.ddns.net/",
    'category': 'Human Resources',
    'version': '1.0',
    'depends': ['hr', 'website_slides'],
    'data': [
        'security/ir.model.access.csv',
        'report/course_certificate_report.xml',
        'views/hr_employee_views.xml',
        'views/certificate_wizard_view.xml',
    ],
    'installable': True,
    'application': False,
}