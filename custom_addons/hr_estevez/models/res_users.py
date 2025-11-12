import logging
from odoo import api, models
from odoo.exceptions import AccessDenied

_logger = logging.getLogger(__name__)

class ResUsers(models.Model):
    _inherit = 'res.users'

    @api.model
    def _get_login_domain(self, login):
        """
        Sobrescribe el método para permitir autenticación con employee_number
        además del login/email tradicional.
        """
        # Primero intenta el dominio normal (por login)
        domain = super()._get_login_domain(login)
        
        # Buscar por employee_number si no se encuentra por login
        # Usamos un OR para buscar tanto por login como por employee_number
        employee_domain = [
            '|',
            ('login', '=', login),
            ('employee_ids.employee_number', '=', login)
        ]
        
        return employee_domain

    @classmethod
    def _login(cls, db, credential, user_agent_env):
        """
        Método alternativo si _get_login_domain no es suficiente.
        Este método busca primero el usuario asociado al employee_number.
        """
        login = credential['login']
        
        try:
            # Intenta el login normal primero
            return super()._login(db, credential, user_agent_env)
        except AccessDenied:
            # Si falla, busca por employee_number
            with cls.pool.cursor() as cr:
                self = api.Environment(cr, 1, {})[cls._name]  # SUPERUSER_ID = 1
                
                # Buscar empleado por número de empleado
                employee = self.env['hr.employee'].sudo().search([
                    ('employee_number', '=', login)
                ], limit=1)
                
                if not employee or not employee.user_id:
                    _logger.info("Login failed: no employee or user found for employee_number %s", login)
                    raise AccessDenied()
                
                # Crear nueva credencial con el login del usuario asociado
                new_credential = dict(credential)
                new_credential['login'] = employee.user_id.login
                
                # Intentar login con el email del usuario encontrado
                return super(ResUsers, cls)._login(db, new_credential, user_agent_env)