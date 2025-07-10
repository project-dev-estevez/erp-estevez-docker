import uuid
import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.addons.google_calendar.utils.google_calendar import GoogleCalendarService
from odoo.addons.google_calendar.models.google_sync import GoogleSync

_logger = logging.getLogger(__name__)

class CalendarEvent(models.Model):
    _inherit = 'calendar.event'

    is_google_meet = fields.Boolean(
        string="Usar Google Meet",
        default=True,
    )
    show_meet_button = fields.Boolean(
        string="Mostrar botón Meet",
        compute="_compute_show_meet_button",
        store=True,
    )

    @api.depends('is_google_meet', 'videocall_location', 'google_id')
    def _compute_show_meet_button(self):
        for event in self:
            event.show_meet_button = (
                event.is_google_meet and 
                not event.videocall_location and 
                bool(event.google_id)
            )

    def _create_google_meet(self):
        """Crea una reunión de Google Meet con manejo mejorado de errores"""
        try:
            service = GoogleCalendarService(self.env['google.service'])
            request_id = str(uuid.uuid4())
            
            _logger.info("Intentando crear Google Meet para evento ID: %s", self.id)
            
            # Crear cuerpo de la solicitud
            body = {
                'conferenceData': {
                    'createRequest': {
                        'conferenceSolutionKey': {'type': 'hangoutsMeet'},
                        'requestId': request_id,
                    }
                }
            }
            
            # Ejecutar la solicitud
            res = service.patch(
                calendar_id='primary',
                event_id=self.google_id,
                body=body,
                params={'conferenceDataVersion': 1},
                timeout=10  # Tiempo de espera en segundos
            )
            
            # Obtener el enlace de Meet
            meet_link = res.get('hangoutLink')
            if meet_link:
                _logger.info("Google Meet creado exitosamente: %s", meet_link)
                return meet_link
            
            # Intentar obtener el enlace de forma alternativa
            conference_data = res.get('conferenceData', {})
            if conference_data:
                for entry_point in conference_data.get('entryPoints', []):
                    if entry_point.get('entryPointType') == 'video':
                        meet_link = entry_point.get('uri')
                        if meet_link:
                            _logger.info("Enlace Meet obtenido de forma alternativa: %s", meet_link)
                            return meet_link
            
            _logger.error("La API de Google no devolvió un enlace Meet. Respuesta: %s", res)
            return False
            
        except Exception as e:
            # Manejar todos los errores de forma genérica
            _logger.exception("Error inesperado creando Google Meet: %s", str(e))
            return False

    def action_force_create_meet(self):
        self.ensure_one()

        # Verificar conexión con Google
        if not self.env.user.google_calendar_token:
            raise UserError(_("Primero debes configurar tu conexión con Google Calendar en tus preferencias de usuario"))
        
        # Verificar datos mínimos del evento
        if not self.start or not self.stop:
            raise UserError(_("El evento debe tener fecha de inicio y fin válidas"))
        if not self.name:
            raise UserError(_("El evento debe tener un título"))
        if not self.user_id.email:
            raise UserError(_("El organizador del evento debe tener un email configurado"))

        # Sincronizar con Google si es necesario
        if not self.google_id:
            try:
                _logger.info("Sincronizando evento con Google Calendar: %s", self.name)
                
                # Forzar sincronización usando el método estándar
                self.need_sync = True
                self.env['calendar.event']._sync_odoo2google(self.env.user)
                
                # Verificar si se obtuvo el ID de Google
                self.env.cache.invalidate()
                self = self.search([('id', '=', self.id)], limit=1)
                
                if not self.google_id:
                    _logger.warning("No se obtuvo google_id después de sincronizar")
                    raise UserError(_("No se pudo sincronizar el evento con Google Calendar. Por favor, guarda el evento e inténtalo de nuevo."))
                    
            except Exception as e:
                _logger.error("Error en sincronización: %s", str(e))
                raise UserError(_("Error de sincronización con Google: %s") % str(e))

        # Crear Meet si no existe
        if not self.videocall_location:
            meet_link = self._create_google_meet()
            if not meet_link:
                # Intentar una segunda vez si falla el primer intento
                _logger.warning("Primer intento fallido, intentando nuevamente...")
                meet_link = self._create_google_meet()
                
                if not meet_link:
                    error_msg = _(
                        "No se pudo generar el enlace de Google Meet. "
                        "Por favor verifica:\n"
                        "1. Tu conexión con Google Calendar está activa\n"
                        "2. Tienes permisos para modificar este evento\n"
                        "3. El evento existe en Google Calendar"
                    )
                    raise UserError(error_msg)
            
            self.write({'videocall_location': meet_link})

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _("Google Meet generado"),
                'message': _("Enlace creado: %s") % self.videocall_location,
                'type': 'success',
                'sticky': False,
                'next': {
                    'type': 'ir.actions.act_window',
                    'res_model': 'calendar.event',
                    'res_id': self.id,
                    'views': [(False, 'form')],
                    'target': 'current',
                }
            }
        }