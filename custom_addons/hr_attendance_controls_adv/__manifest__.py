# -*- coding: utf-8 -*-
#################################################################################
# Author      : CFIS (<https://www.cfis.store/>)
# Copyright(c): 2017-Present CFIS.
# All Rights Reserved.
#
#
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#
# You should have received a copy of the License along with this program.
# If not, see <https://www.cfis.store/>
#################################################################################

{
    "name": """
        HR Attendance Control | HR Attendance Face recognition | HR Attendance Geospatial Control | 
        HR Attendance Photo | HR Attendance Reason | HR Attendance Geolocation |
        HR Attendance Geofence | HR Attendance IP Address | Geolocation | Geofence |
        Face Recognition | IP Address | Reason
    """,
    "summary": """
        This module allows the odoo Hr Attendance Manager / Administrators to define a virtual geographic boundary for 
        attendance locations, and employees can only check in and out within one of these Geofence areas. Additionally, 
        the module will record employee geolocation, geofence, face rRecognition with photo, IP address, and check in/out reasons.
    """,
    "version": "18.1",
    "description": """
        This module allows the odoo Hr Attendance Manager / Administrators to define a virtual geographic boundary for 
        attendance locations, and employees can only check in and out within one of these Geofence areas. Additionally, 
        the module will record employee geolocation, geofence, face rRecognition with photo, IP address, and check in/out reasons.
        Geolocation
        Geofence 
        Photo   
        IP Address
        Check In - Check Out Reasons
        Face Recognition
    """,    
    "author": "CFIS",
    "maintainer": "CFIS",
    "license" :  "Other proprietary",
    "website": "https://www.cfis.store",
    "images": ["images/hr_attendance_controls_adv.png"],
    "category": "Human Resources",
    "depends": [
        "base",
        "hr_attendance",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/geolocation_data.xml",
        "views/res_config_settings.xml",
        "views/hr_attendance_reasons_view.xml",
        "views/hr_attendance_geofence.xml",
        # "views/hr_attendance_views.xml",
        "views/hr_employee_views.xml",        
    ],
    "assets": {
        "web.assets_backend": [
            "/hr_attendance_controls_adv/static/src/js/*.*",
        ],
        "hr_attendance.assets_public_attendance":[
            "/hr_attendance_controls_adv/static/src/js/attendance_recognition_dialog.js",
            "/hr_attendance_controls_adv/static/src/js/attendance_recognition_dialog.xml",
            "/hr_attendance_controls_adv/static/src/js/public_kiosk_app.scss",
            "/hr_attendance_controls_adv/static/src/js/public_kiosk_app.js",
            "/hr_attendance_controls_adv/static/src/js/public_kiosk_app.xml",
        ]
    },   
    "installable": True,
    "application": True,
    "price"                 :  260.00,
    "currency"              :  "EUR",
    "pre_init_hook"         :  "pre_init_check",
    'uninstall_hook': 'uninstall_hook',
}
