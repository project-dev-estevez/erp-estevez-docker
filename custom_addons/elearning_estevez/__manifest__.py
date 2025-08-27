{
    'name': 'Elearning Estevez',
    'version': '18.0.1.0.0',
    'author': 'Tu Nombre / Empresa',
    'website': 'https://estevez-erp.ddns.net/',
    'category': 'Website/Elearning',
    'summary': 'Personalización de formulario de cursos (eLearning)',
    'description': 'Agrega campos personalizados al formulario de cursos en Odoo eLearning.',
    'depends': ['website_slides', 'hr'],
    'data': [
        'views/slide_channel_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
