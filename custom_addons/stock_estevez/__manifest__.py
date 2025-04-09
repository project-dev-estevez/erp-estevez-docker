{
    'name': 'Stock Estevez',
    'version': '1.0',
    'summary': 'Modulo stock de Estevez',
    'depends': ['stock', 'base', 'hr'],
    'author': 'Estevez.Jor',
    'category': 'Inventory',
    'data': [
        'security/ir.model.access.csv',
        'views/stock_warehouse_requisition_views.xml',
        'views/stock_menu.xml'
    ],
    'installable': True,
    'application': False, 
}