{
    'name': 'Formulario Productos',
    'version': '1.0',
    'summary': 'crea y elimina campos en el formulario de productos',
    'depends': ['product','account'],
    'author': 'Estevez.Jor',
    'category': 'Sales',
    'description': """
        Este módulo crea y elimina la opción de ventas del formulario de productos.
    """,
    'data': [
        'views/product_views.xml',
    ],
    'installable': True,
    'application': False,
}