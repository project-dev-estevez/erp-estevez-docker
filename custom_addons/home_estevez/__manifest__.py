# -*- coding: utf-8 -*-
{
    'name': 'Home Estevez',
    'version': '1.2.0',
    'category': 'Web',
    'license': 'LGPL-3',
    'summary': 'Pantalla de inicio, barra superior y menú lateral con la marca Estevez.Jor',
    'description': """
        Rediseño del menú de aplicaciones de MuK (muk_web_theme):
        - Saludo con el nombre del usuario y la fecha del día
        - Buscador de aplicaciones
        - Tarjetas de aplicaciones con efecto al pasar el cursor
        - Colores y logo de Estevez.Jor
        - Barra superior y menú lateral (muk_web_appsbar) con la marca
        - Botón para comprimir el menú lateral a solo íconos
    """,
    'author': 'Estevez',
    'website': '',
    'depends': ['muk_web_theme'],
    'data': [],
    'assets': {
        'web.assets_backend': [
            'home_estevez/static/src/home_menu/home_menu.scss',
            'home_estevez/static/src/home_menu/home_menu.xml',
            'home_estevez/static/src/home_menu/home_menu.js',
            'home_estevez/static/src/navigation/navigation.scss',
            'home_estevez/static/src/navigation/appsbar.xml',
            'home_estevez/static/src/navigation/appsbar.js',
        ],
    },
    'installable': True,
    'application': False,
}
