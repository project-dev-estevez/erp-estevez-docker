# -*- coding: utf-8 -*-
{
    'name': 'Custom Inputs Estevez',
    'version': '1.0.0',
    'category': 'Web',
    'summary': 'Personalización global de estilos para campos input en Odoo',
    'description': """
        Módulo para aplicar estilos personalizados de forma global a todos los campos
        de entrada (input) en el backend de Odoo.
        
        Características:
        - Estilos consistentes en todos los formularios
        - Bordes azules y esquinas redondeadas
        - Efectos interactivos (hover y focus)
        - Aplicación solo en el backend
    """,
    'author': 'Estevez',
    'website': '',
    'depends': ['web'],
    'data': [],
    'assets': {
        'web.assets_backend': [
            'custom_inputs_estevez/static/src/scss/custom_inputs.scss',
        ],
    },
    'installable': True,
    'auto_install': False,
    'application': False,
}
