{
    'name': 'Stock Estevez',
    'version': '1.0',
    'summary': 'Modulo stock de Estevez',
    'depends': ['base', 'stock', 'product', 'uom', 'hr', 'mail'],
    'author': 'Estevez.Jor',
    'category': 'Inventory',
    'data': [
        'data/mail_templates.xml', 
        'data/stock_estevez_categories.xml',       
        'security/security.xml',
        'data/mail_templates.xml',
        'data/stock_sequence.xml',
        'security/ir.model.access.csv',
        'views/return_order.xml',
        'views/stock_warehouse_requisition_views.xml',
        'views/stock_assignment_views.xml',
        'views/stock_menu.xml',
        'views/stock_warehouse.xml'
    ],
    'installable': True,
    'application': False, 
}