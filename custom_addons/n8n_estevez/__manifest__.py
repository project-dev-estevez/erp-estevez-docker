{
    'name': 'n8n Estevez',
    'version': '1.0.0',
    'summary': 'Incrusta el chat de IA de n8n en el backend de Odoo',
    'author': 'Equipo Estevez',
    'category': 'Tools',
    'depends': ['base', 'web'],
    'data': [],
    'assets': {
        'web.assets_backend': [
            '/n8n_estevez/static/src/js/n8n_chat.js',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
}