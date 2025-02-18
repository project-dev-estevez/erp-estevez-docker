# nombre_del_modulo/__manifest__.py
{
    'name': 'Providers',
    'version': '1.0',
    'summary': 'Modulo de proveedores en EstevezJor',
    'description': 'Registro de un nuevo proveedor',
    'author': "Estevez.Jor",
    'website': "https://estevez-erp.ddns.net/",
    'category': 'Purchase',
    'version': '0.2',
    'depends': ['base', 'purchase'],  # Dependencias del módulo
    'data': [
                
         'views/res_partner_industry_data.xml',  # Archivo de datos        
        'views/res_partner_views.xml',
    ],   
    'assets': {
    'web.assets_backend': [
        'form_providers/static/src/js/confirmation_modal.js',
    ],
},
}