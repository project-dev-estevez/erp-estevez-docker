# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request


class WebManifestCustom(http.Controller):
    
    @http.route('/web/manifest.webmanifest', type='http', auth='public', methods=['GET'])
    def web_app_manifest(self):
        """
        Customiza el manifest de la PWA con los iconos personalizados de Estevez
        """
        manifest = {
            'name': 'Estevez.Jor',
            'short_name': 'Estevez',
            'description': 'Sistema ERP Estevez',
            'scope': '/web',
            'start_url': '/web',
            'display': 'standalone',
            'background_color': '#714B67',
            'theme_color': '#714B67',
            'icons': [
                {
                    'src': '/custom_inputs_estevez/static/src/img/icon.png',
                    'sizes': '64x64',
                    'type': 'image/png',
                },
                {
                    'src': '/custom_inputs_estevez/static/src/img/odoo-icon-192x192.png',
                    'sizes': '192x192',
                    'type': 'image/png',
                    'purpose': 'any maskable',
                },
                {
                    'src': '/custom_inputs_estevez/static/src/img/odoo-icon-512x512.png',
                    'sizes': '512x512',
                    'type': 'image/png',
                    'purpose': 'any maskable',
                },
            ],
        }
        
        return request.make_json_response(manifest)
