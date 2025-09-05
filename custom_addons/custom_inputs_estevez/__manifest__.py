# -*- coding: utf-8 -*-
{
    'name': 'Custom Inputs Estevez',
    'version': '1.0.0',
    'category': 'Web',
    'summary': 'Personalización global de estilos y spinner en Odoo',
    'description': """
        Módulo para aplicar estilos personalizados a los campos input y
        un spinner global para llamadas RPC y navegación UI en el backend.
    """,
    'author': 'Estevez',
    'website': '',
    'depends': ['web'],
    'data': [],
    'assets': {
        'web.assets_backend': [
            'custom_inputs_estevez/static/src/scss/custom_inputs.scss',
            'custom_inputs_estevez/static/src/css/custom_spinner.css',
            'custom_inputs_estevez/static/src/js/custom_spinner.js',
        ],
    },
    'installable': True,
    'application': False,
}
