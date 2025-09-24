# -*- coding: utf-8 -*-
{
    "name": "HR Attendance Estevez Custom",
    "summary": "Personalización módulo IA asistencias (hereda hr_attendance_controls_adv)",
    "version": "1.0.0",
    "author": "Estevez.Jor",
    "category": "Human Resources",
    "depends": ["hr_attendance_controls_adv"],
    "data": [
        "views/hr_attendance_view_form_inherit.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "hr_attendance_estevez/static/src/xml/attendance_menu_inherit.xml",
            "hr_attendance_estevez/static/src/xml/attendance_systray_inherit.xml",
            "hr_attendance_estevez/static/src/js/attendance_menu_patch.js",
        ],
    },
    "installable": True,
    "application": False,
}
