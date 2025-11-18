# -*- coding: utf-8 -*-
import logging
from odoo import http
from odoo.http import request
from werkzeug.utils import redirect

_logger = logging.getLogger(__name__)


class PasswordChangeController(http.Controller):
    """
    Controlador para el cambio obligatorio de contraseña en primer login
    """
    
    @http.route('/web/change_password_required', type='http', auth='user', website=True)
    def change_password_page(self, error=None, **kw):
        """
        Renderiza la página de cambio de contraseña obligatorio
        """
        user = request.env.user
        
        # Verificar si realmente necesita cambiar contraseña
        if user.password_changed or '@' in (user.login or ''):
            _logger.info(f"Usuario {user.login} no requiere cambio de contraseña, redirigiendo...")
            return redirect('/web')
        
        _logger.info(f"Mostrando página de cambio de contraseña para: {user.login}")
        
        return request.render('hr_estevez.password_change_required_template', {
            'user_name': user.name,
            'user_login': user.login,
            'error': error,
        })
    
    @http.route('/web/change_password_submit', type='http', auth='user', methods=['POST'], csrf=True)
    def change_password_submit(self, new_password, confirm_password, **kw):
        """
        Procesa el cambio de contraseña (POST tradicional)
        """
        user = request.env.user
        
        # Validaciones
        if not new_password or not confirm_password:
            return self.change_password_page(error='Por favor complete todos los campos')
        
        if len(new_password) < 8:
            return self.change_password_page(error='La contraseña debe tener al menos 8 caracteres')
        
        if new_password != confirm_password:
            return self.change_password_page(error='Las contraseñas no coinciden')
        
        try:
            # Cambiar la contraseña
            user.sudo().write({
                'password': new_password,
                'password_changed': True
            })
            
            _logger.info(f"✅ Contraseña cambiada exitosamente para usuario: {user.login}")
            
            # Redirigir con mensaje de éxito
            return redirect('/web?password_changed=success')
            
        except Exception as e:
            _logger.error(f"Error al cambiar contraseña para {user.login}: {str(e)}")
            return self.change_password_page(error=f'Error al cambiar la contraseña: {str(e)}')