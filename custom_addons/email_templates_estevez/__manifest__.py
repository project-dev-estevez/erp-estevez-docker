{
    "name": "Personalización de Emails Estevez.Jor",
    # The first 2 numbers are Odoo major version, the last 3 are x.y.z version of the module.
    "version": "18.0.1.0.0",
    'summary': 'Personaliza los correos electrónicos de Odoo',
    "depends": ['auth_signup'],
    "author": "Estevez.Jor",
    # Categories are freeform, for existing categories visit https://github.com/odoo/odoo/blob/17.0/odoo/addons/base/data/ir_module_category_data.xml
    'category': 'Tools',
    "description": """
    Personalización de Emails Estevez.Jor
    """,
    'data': [
        'views/reset_password_email_views.xml',
    ],
    "application": False,
    "installable": True,
    "auto_install": False,
    "license": "LGPL-3",
}