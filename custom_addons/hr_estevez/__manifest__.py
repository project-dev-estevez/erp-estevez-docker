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
    'depends': ['hr', 'hr_contract', 'stock', 'product', 'stock_estevez'],

    # always loaded
    'data': [
        # Archivos de datos
        'security/ir.model.access.csv',

        # Archivos de informes
        'report/hr_employee_remision_report.xml',
        'report/hr_employee_remision_report_templates.xml',
        'report/hr_employee_convenio_salida_report.xml',
        'report/hr_employee_convenio_salida_report_templates.xml',
        'report/hr_employee_carta_patronal_report.xml',
        'report/hr_employee_carta_patronal_report_templates.xml',
        'report/hr_contract_addendum_report.xml',
        'report/hr_contract_addendum_report_templates.xml',
        'report/hr_contract_report.xml',
        'report/hr_contract_report_templates.xml',
        'report/hr_employee_memorandum_report.xml',
        'report/hr_employee_memorandum_report_templates.xml',
        'report/hr_employee_loan_report.xml',
        'report/hr_employee_loan_report_templates.xml',

        # Email Templates
        # 'data/email_template_contract_expired.xml',

        # Cron Jobs
        'data/cron_notify_expired_contracts.xml',

        # Archivos de Vistas
        'views/hr_job_views.xml',
        'views/hr_direction_views.xml',
        'views/hr_department_views.xml',
        'views/hr_area_views.xml',
        'views/hr_employee_menu.xml',
        'views/hr_employee_views.xml',
        'views/hr_contract_views.xml',
        'views/hr_memorandum_views.xml',
        'views/hr_loan_views.xml',
        'views/hr_employee_archive_wizard_views.xml',
        'views/hr_employee_reactivate_wizard_views.xml',
        'views/hr_employee_history_views.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'hr_estevez/static/src/css/custom_styles.css',
        ],
    },
}

