import logging
from odoo import api, fields, models
from odoo.exceptions import AccessDenied

_logger = logging.getLogger(__name__)

class ResUsers(models.Model):
    _inherit = 'res.users'
    
    # Campo para rastrear si el usuario ya cambió su contraseña predeterminada
    password_changed = fields.Boolean(
        string='Contraseña Cambiada',
        default=True,
        help='Indica si el usuario ya cambió su contraseña predeterminada. '
             'False significa que debe cambiar la contraseña en el primer login.'
    )

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
            
    @api.model_create_multi
    def create(self, vals_list):
        """
        Sobrescribe create para manejar la creación de usuarios desde empleados.
        
        Flujos:
        1. Usuario con email: Flujo normal de Odoo (invitación por correo)
        2. Usuario sin email (solo employee_number): Asignar contraseña por defecto '12345678'
        """
        for vals in vals_list:
            # Detectar si se está creando desde un empleado sin email
            if self._context.get('default_no_email_employee'):
                employee_id = self._context.get('default_create_employee_id')
                login = vals.get('login', '')
                
                # Validar que el login no sea un email
                if '@' not in login:
                    # Asignar contraseña por defecto
                    if not vals.get('password'):
                        vals['password'] = '12345678'
                        # Marcar que la contraseña NO ha sido cambiada
                        vals['password_changed'] = False
                        
                        _logger.info(
                            f"🔑 Asignando contraseña por defecto '12345678' para usuario: {login} "
                            f"(Empleado ID: {employee_id})"
                        )
                        _logger.info(
                            f"💡 IMPORTANTE: El usuario puede hacer login con:\n"
                            f"   - Usuario: {login}\n"
                            f"   - Contraseña: 12345678\n"
                            f"   Se recomienda que el empleado cambie esta contraseña después del primer login."
                        )
                else:
                    _logger.warning(
                        f"⚠️ Contexto 'default_no_email_employee' activo pero login parece ser email: {login}"
                    )
            
            # Logging para usuarios con email (flujo normal)
            elif self._context.get('default_create_employee_id') and '@' in vals.get('login', ''):
                employee_id = self._context.get('default_create_employee_id')
                _logger.info(
                    f"📧 Creando usuario con email para empleado ID {employee_id}: {vals.get('login')} - "
                    f"Se enviará invitación por correo"
                )
        
        # Llamar al create original
        users = super(ResUsers, self).create(vals_list)
        
        # Asignar rol "Empleado: Asistencias" si se está creando desde un empleado
        for user in users:
            if self._context.get('default_create_employee_id'):
                self._assign_employee_role(user)
                # Forzar que solo tenga los grupos del rol asignado
                user.set_groups_from_roles(force=True)
        
        return users
    
    def _assign_employee_role(self, user):
        """
        Asigna automáticamente el rol 'Empleado: Asistencias' al usuario creado desde empleado.
        """
        try:
            # Buscar el rol por nombre
            employee_role = self.env['res.users.role'].sudo().search([
                ('name', 'ilike', 'Empleado%Asistencias')
            ], limit=1)
            
            if not employee_role:
                _logger.warning("⚠️ No se encontró el rol 'Empleado: Asistencias'")
                return
            
            # Crear la línea de rol para el usuario
            self.env['res.users.role.line'].sudo().create({
                'user_id': user.id,
                'role_id': employee_role.id,
                'is_enabled': True,
            })
            
            _logger.info(
                f"✅ Rol '{employee_role.name}' asignado exitosamente al usuario: {user.login}"
            )
            
        except Exception as e:
            _logger.error(f"❌ Error al asignar rol al usuario {user.login}: {str(e)}")
    
    def write(self, vals):
        """
        Sobrescribe write para detectar cambio de contraseña
        y marcar password_changed = True
        """
        # Si se está cambiando la contraseña, marcar como cambiada
        if 'password' in vals:
            vals['password_changed'] = True
            _logger.info(f"🔄 Contraseña cambiada para usuario(s): {self.mapped('login')}")
        
        return super(ResUsers, self).write(vals)