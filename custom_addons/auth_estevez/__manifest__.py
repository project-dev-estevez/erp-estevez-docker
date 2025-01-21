{
    "name": "Authentication Estevez.Jor",
    # The first 2 numbers are Odoo major version, the last 3 are x.y.z version of the module.
    "version": "18.0.1.0.0",
    "depends": ["web", "auth_signup"],
    "author": "Estevez.Jor",
    # Categories are freeform, for existing categories visit https://github.com/odoo/odoo/blob/17.0/odoo/addons/base/data/ir_module_category_data.xml
    "category": "Customizations",
    "description": """
    Auth Extension For Estevez.Jor
    """,
    # data files always loaded at installation
    "data": [
        "views/res_config_settings_views.xml",
        "views/login_templates.xml"
    ],
    "assets": {
        "web.assets_frontend": [
            ('include', 'web._assets_bootstrap_frontend'),
            "auth_estevez/static/fonts/poppins.css",
            "auth_estevez/static/src/scss/login.scss",
        ],
    },
    "application": False,
    "installable": True,
    "auto_install": False,
    "license": "LGPL-3",
}