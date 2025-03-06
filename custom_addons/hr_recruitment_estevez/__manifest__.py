# -*- coding: utf-8 -*-
{
    "name": "Reclutamiento Estevez",
    "summary": "Extensión del módulo de reclutamiento para Estevez.Jor",
    "description": """
        Este módulo extiende el módulo de reclutamiento para agregar la lógica de negocio de Estevez.Jor
    """,
    "author": "Estevez.Jor",
    "website": "https://estevezjorinternacional.com",
    "category": "Human Resources",
    "version": "0.1",
    "depends": ['base', 'hr', 'hr_estevez', 'hr_recruitment', 'utm'],
    "data": [
        "security/ir.model.access.csv",
        "security/hr_recruitment_security.xml",
        'report/hr_applicant_doctor_report_templates.xml',
        'report/hr_applicant_doctor_report.xml',
        'views/hr_applicant_view_form_inherit.xml',
        "views/hr_requisition_views.xml",
        "data/hr_requisition_uniform_data.xml",
        "data/hr_requisition_epp_data.xml"
    ],
    "installable": True,
    "application": False,
    "i18n": ["i18n/es_419.po", "i18n/es.po"],
}