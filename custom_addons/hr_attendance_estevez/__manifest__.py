# -*- coding: utf-8 -*-
{
    "name": "HR Attendance Estevez Custom",
    "summary": "Personalización módulo IA asistencias (hereda hr_attendance_controls_adv)",
    "version": "1.0.0",
    "author": "Estevez.Jor",
    "website": "https://www.estevezjor.mx",
    "company": "Estevez.Jor",
    "maintainer": "Estevez.Jor",
    "category": "Human Resources",
    "depends": ["base", "report_xlsx", "hr", "hr_holidays", "hr_attendance", "hr_attendance_controls_adv"],
    "data": [
        "security/hr_attendance_security.xml",
        "security/ir.model.access.csv",
        "data/ir_cron_data.xml",  # 🕚 Cronjob para cerrar asistencias automáticamente
        'data/attendance_tag_data.xml',
        "views/hr_attendance_view_form_inherit.xml",
        "views/hr_attendance_list_management_inherit.xml",
        "views/hr_attendance_employee_views.xml",
        "views/hr_attendance_photo_wizard.xml",
        "views/hr_attendance_location_wizard.xml",
        "views/hr_attendance_reject_wizard.xml",
        "views/hr_attendance_approve_wizard.xml",
        "views/hr_attendance_log_wizard.xml",

        # Dashboard
        "views/hr_leave_type_views.xml",
        "views/advance_hr_attendance_dashboard_menus.xml",
        "views/res_config_settings_views.xml",
        "report/hr_attendance_reports.xml",
        "report/hr_attendance_templates.xml",

        # Wizards Reports
        'views/wizards/payroll_report_wizard_views.xml',
        'views/wizards/attendance_report_wizard_views.xml',
        'views/reports/report_actions.xml',
    ],
    'assets': {
        "web.assets_backend": [
            "hr_attendance_estevez/static/src/xml/attendance_dashboard_templates.xml",
            "hr_attendance_estevez/static/src/js/attendance_dashboard.js",
            "hr_attendance_estevez/static/src/scss/attendance_dashboard.scss",
        ],
    },
    "external_dependencies": {
        "python": ["pandas"],
    },
    "license": "AGPL-3",
    "installable": True,
    "auto_install": False,
    "application": False,
}
