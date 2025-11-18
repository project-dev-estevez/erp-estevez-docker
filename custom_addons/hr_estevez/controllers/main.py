# -*- coding: utf-8 -*-
import logging
from odoo import http
from odoo.http import request
from odoo.addons.web.controllers.home import Home

_logger = logging.getLogger(__name__)


class HomeInherit(Home):
    """
    Hereda del controlador Home de Odoo para interceptar el login
    y redirigir usuarios en su primer login a cambiar contraseña
    """
    
    @http.route()
    def web_login(self, *args, **kw):
        """
        Intercepta el proceso de login para detectar primer login
        y redirigir automáticamente al wizard de cambio de contraseña
        """
        # Llamar al método original del padre
        response = super(HomeInherit, self).web_login(*args, **kw)
        
        # Verificar si el usuario se autenticó exitosamente
        if request.session.uid:
            user = request.env['res.users'].sudo().browse(request.session.uid)
            
            _logger.info(f"🔍 Usuario autenticado: {user.login}")
            _logger.info(f"   📅 login_date: {user.login_date}")
            _logger.info(f"   📧 Tiene '@' en login: {'@' in user.login if user.login else 'N/A'}")
            _logger.info(f"   🔐 password_changed: {user.password_changed}")
            
            # Detectar primer login:
            # - login NO contiene '@' (es employee_number, no email)
            # - password_changed es False (aún no ha cambiado la contraseña predeterminada)
            if user.login and '@' not in user.login and not user.password_changed:
                _logger.info(f"🔐 PRIMER LOGIN detectado para usuario: {user.login}")
                _logger.info(f"   ↪️  Redirigiendo a página de cambio de contraseña...")
                
                return request.redirect('/web/change_password_required')
            else:
                _logger.info(f"✅ Login normal (contraseña ya cambiada o usuario con email)")
        
        return response
