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
                _logger.info(f"   ↪️  Abriendo wizard de cambio de contraseña...")
                
                # Crear el wizard de cambio de contraseña (change.password.own)
                # Este wizard permite al usuario cambiar su propia contraseña sin verificación previa
                try:
                    wizard = request.env['change.password.own'].sudo().create({})
                    wizard_id = wizard.id
                    
                    _logger.info(f"   ✅ Wizard creado (ID: {wizard_id})")
                    
                    # Redirigir al wizard en modo formulario con título personalizado
                    # create=false oculta el botón "New"
                    # title personaliza el título de la ventana
                    return request.redirect(
                        f'/web#id={wizard_id}&model=change.password.own&view_type=form&cids=1&menu_id='
                        f'&create=false&edit=true'
                    )
                except Exception as e:
                    _logger.error(f"   ❌ Error al crear wizard: {str(e)}")
                    # Fallback: redirigir a preferencias
                    action_id = request.env.ref('base.action_res_users_my').id
                    return request.redirect(f'/web#id={user.id}&action={action_id}&model=res.users&view_type=form')
            else:
                _logger.info(f"✅ Login normal (contraseña ya cambiada o usuario con email)")
        
        return response
