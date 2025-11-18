# -*- coding: utf-8 -*-
{
    'name': "RH Estevez",
    
    'license': 'LGPL-3',

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
    'depends': ['base', 'hr', 'hr_holidays', 'hr_contract', 'stock', 'product', 'stock_estevez', 'custom_training_extension', 'web'],

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
        'views/hr_user_base_inherit_views.xml',
        'views/res_users_create_wizard_inherit.xml',
        'views/password_change_template.xml',
        'views/hr_job_views.xml',
        'views/hr_direction_views.xml',
        'views/hr_department_views.xml',
        'views/hr_area_views.xml',
        'views/hr_employee_menu.xml',
        'views/hr_employee_views.xml',
        'views/hr_contract_views.xml',
        'views/hr_memorandum_views.xml',
        'views/hr_loan_views.xml',
        'views/hr_employee_documents_kanban.xml',
        'views/view_attachment_form_custom.xml',
        'views/hr_employee_reactivate_wizard_views.xml',
        'views/hr_employee_archive_wizard_views.xml',
        'views/hr_employee_history_views.xml',
        'views/hr_leave.xml',
        'views/hr_leave_type_views.xml',
        'views/hr_vacation_period_views.xml',
        'views/hr_time_off_in_lieu_views.xml',       
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'hr_estevez/static/src/components/**/*.js',
            'hr_estevez/static/src/components/**/*.xml',
        ],
    },
}

