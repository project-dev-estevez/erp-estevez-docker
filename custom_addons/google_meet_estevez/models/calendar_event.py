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
        """Crea una reunión de Google Meet con los nuevos permisos"""
        try:
            service = GoogleCalendarService(self.env['google.service'])
            request_id = str(uuid.uuid4())
            
            _logger.info("Creando Google Meet para evento: %s", self.name)
            
            # Solicitud mejorada con los nuevos scopes
            body = {
                'conferenceData': {
                    'createRequest': {
                        'conferenceSolutionKey': {'type': 'hangoutsMeet'},
                        'requestId': request_id,
                        'requestStatus': 'pending'  # Nuevo parámetro que puede ayudar
                    }
                }
            }
            
            res = service.patch(
                calendar_id='primary',
                event_id=self.google_id,
                body=body,
                params={
                    'conferenceDataVersion': 1,
                    'sendUpdates': 'none'  # Evita notificaciones innecesarias
                },
                timeout=15
            )
            
            # Búsqueda mejorada del enlace
            meet_link = (
                res.get('hangoutLink') or
                res.get('conferenceData', {}).get('entryPoints', [{}])[0].get('uri') or
                res.get('conferenceData', {}).get('conferenceUri')
            )
            
            if meet_link:
                _logger.info("Meet creado exitosamente: %s", meet_link)
                return meet_link
            
            _logger.warning("La API no devolvió enlace directo. Buscando alternativas...")
            return self._find_meet_link_in_response(res)
            
        except Exception as e:
            _logger.error("Error creando Meet: %s", str(e))
            return False

    def _find_meet_link_in_response(self, response):
        """Busca en profundidad el enlace de Meet en la respuesta"""
        # 1. Buscar en conferenceData
        conference_data = response.get('conferenceData', {})
        if conference_data:
            for entry_point in conference_data.get('entryPoints', []):
                if entry_point.get('entryPointType') == 'video':
                    return entry_point.get('uri')
        
        # 2. Buscar en la descripción
        description = response.get('description', '')
        if 'meet.google.com' in description:
            return description.split('meet.google.com')[0] + 'meet.google.com' + description.split('meet.google.com')[1].split()[0]
        
        # 3. Buscar en location
        location = response.get('location', '')
        if 'meet.google.com' in location:
            return location
        
        _logger.error("No se encontró enlace Meet en la respuesta: %s", response)
        return False

    def action_force_create_meet(self):
        self.ensure_one()

        # Verificación de conexión
        if not self.env.user.google_calendar_token:
            raise UserError(_("Configura tu conexión con Google Calendar primero"))
        
        # Validación básica del evento
        required_fields = ['start', 'stop', 'name', 'user_id.email']
        if any(not getattr(self, field.split('.')[0]) for field in required_fields):
            raise UserError(_("Faltan datos requeridos en el evento"))

        # Sincronización con Google si es necesario
        if not self.google_id:
            self._sync_with_google()
        
        # Crear Meet
        if not self.videocall_location:
            meet_link = self._create_google_meet()
            if not meet_link:
                raise UserError(_("""
                No se pudo generar el Meet. Verifica:
                1. Que tienes permisos para modificar eventos en Google Calendar
                2. Que el evento existe en tu calendario
                3. Que la API de Google Meet está habilitada
                """))
            
            self.videocall_location = meet_link

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _("✅ Meet Generado"),
                'message': _("Enlace: <a href='%s' target='_blank'>%s</a>") % (self.videocall_location, self.videocall_location),
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

    def _sync_with_google(self):
        """Manejo mejorado de sincronización"""
        try:
            _logger.info("Sincronizando evento: %s", self.name)
            self.need_sync = True
            self.env['calendar.event']._sync_odoo2google(self.env.user)
            self.env.cache.invalidate()
            self = self.search([('id', '=', self.id)])
            
            if not self.google_id:
                raise UserError(_("Sincronización fallida. Revisa tu conexión con Google"))
        except Exception as e:
            _logger.exception("Error en sincronización: %s", str(e))
            raise UserError(_("Error sincronizando con Google: %s") % str(e))