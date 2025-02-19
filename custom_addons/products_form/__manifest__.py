{
    'name': 'Formulario Productos',
    'version': '1.0',
    'summary': 'crea y elimina campos en el formulario de productos',
    'depends': ['product','account','purchase'],
    'author': 'Estevez.Jor',
    'category': 'Sales',
    'description': """
        Este módulo crea y elimina la opción de ventas del formulario de productos.
    """,
    'data': [
        'security/ir.model.access.csv',
        'views/product_views.xml',
        'views/purchase_requisition_views.xml',
        'views/purchase_menu.xml',
        
    ],
    'installable': True,
    'application': False,
}