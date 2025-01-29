# -*- coding: utf-8 -*-
{
    'name': "RH Estevez",

    'summary': "Extensión del módulo de empleados para Estevez.Jor",

    'description': """
        Este módulo extiende el módulo de empleados para agregar la lógica de negocio de Estevez.Jor
    """,

    'author': "Estevez.Jor",
    'website': "https://estevez-erp.ddns.net/",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Human Resources',
    'version': '0.2',

    # any module necessary for this one to work correctly
    'depends': ['hr', 'hr_contract'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/hr_direction_views.xml',
        'views/hr_department_views.xml',
        'views/hr_area_views.xml',
        'views/hr_employee_menu.xml',
        'views/hr_employee_views.xml',
        'views/hr_contract_views.xml',
        'views/hr_job_views.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}

