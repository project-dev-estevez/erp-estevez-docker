# -*- coding: utf-8 -*-
{
    'name': 'Custom Inputs Estevez',
    'version': '1.1.0',
    'category': 'Web',
    'license': 'LGPL-3',
    'summary': 'Personalización global de estilos, spinner y logos PWA en Odoo',
    'description': """
        Módulo para aplicar estilos personalizados a los campos input,
        un spinner global para llamadas RPC y navegación UI en el backend,
        y personalización de logos e iconos para PWA (Progressive Web App).
        
        Características:
        - Estilos personalizados en inputs
        - Spinner customizado
        - Logos e iconos personalizados para PWA
        - Favicon personalizado
        - Manifest.json customizado para instalación en escritorio/móvil
    """,
    'author': 'Estevez',
    'website': '',
    'depends': ['mail', 'web'],
    'data': [],
    'assets': {
        'web.assets_backend': [
            'custom_inputs_estevez/static/src/scss/custom_inputs.scss',
            'custom_inputs_estevez/static/src/css/custom_spinner.css',
            'custom_inputs_estevez/static/src/js/custom_spinner.js',
            'custom_inputs_estevez/static/img/odoo-icon-192x192.png',
            'custom_inputs_estevez/static/img/odoo-icon-512x512.png',
            'custom_inputs_estevez/static/src/js/remove_test_paragraphs.js',
        ],
        "web.assets_frontend": [
            'custom_inputs_estevez/static/img/favicon.ico',
        ]
    },
    'installable': True,
    'application': False,
}
