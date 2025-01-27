{
    "name": "Menú Principal Estevez.Jor",
    # The first 2 numbers are Odoo major version, the last 3 are x.y.z version of the module.
    "version": "18.0.1.0.0",
    'summary': 'Personaliza el menú principal de Odoo',
    "depends": ["web", "auth_signup"],
    "author": "Estevez.Jor",
    # Categories are freeform, for existing categories visit https://github.com/odoo/odoo/blob/17.0/odoo/addons/base/data/ir_module_category_data.xml
    "category": "Theme/Backend",
    "description": """
    Menú Principal de Estevez.Jor
    """,
    'data': ['views/custom_muk_menu.xml'],
    "application": False,
    "installable": True,
    "auto_install": False,
    "license": "LGPL-3",
    "images": ["static/img/logo.png"],
}