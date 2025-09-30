# -*- coding: utf-8 -*-
{
    "name": "HR Attendance Estevez Custom",
    "summary": "Personalización módulo IA asistencias (hereda hr_attendance_controls_adv)",
    "version": "1.0.0",
    "author": "Estevez.Jor",
    "category": "Human Resources",
    "depends": ["hr_attendance_controls_adv"],
    "data": [
        "security/hr_attendance_security.xml",
        "security/ir.model.access.csv",
        "views/hr_attendance_view_form_inherit.xml",
        "views/hr_attendance_list_management_inherit.xml",
        "views/hr_attendance_photo_wizard.xml",
        "views/hr_attendance_location_wizard.xml",
        "views/hr_attendance_reject_wizard.xml",
        "views/hr_attendance_approve_wizard.xml",
        "views/hr_attendance_log_wizard.xml",
    ],
        'assets': {
            'web.assets_backend': [
                # Incluye los assets originales como dependencia explícita
                'hr_attendance_estevez/static/src/components/**/*.xml',
                'hr_attendance_estevez/static/src/components/**/*.scss',
                'hr_attendance_estevez/static/src/components/**/*.js',
            ],
    },
    "installable": True,
    "application": False,
}
