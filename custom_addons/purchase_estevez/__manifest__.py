{
    'name': 'Compras Estevez',
    'version': '1.0',
    'summary': 'Modulo compras de Estevez',
    'depends': ['product','account','purchase', 'base', 'account'],
    'author': 'Estevez.Jor',
    'category': 'Purchases',
    'description': """
        Este módulo extiende el módulo de compras para agregar la lógica de negocio de Estevez.Jor
    """,
    'data': [
        'security/ir.model.access.csv',
        'views/product_views.xml',
        'views/purchase_requisition_views.xml',
        'views/purchase_menu.xml',
        'views/res_partner_industry_data.xml',      
        'views/res_partner_views.xml',
        
    ],
    
    'installable': True,
    'application': False,
}