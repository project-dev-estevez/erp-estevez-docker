import uuid
import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.addons.google_calendar.utils.google_calendar import GoogleCalendarService
from odoo.addons.google_calendar.models.google_sync import GoogleSync
from datetime import timedelta
import json

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
    videocall_location = fields.Char(string="Enlace Meet")

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
            _logger.debug("Google ID del evento: %s", self.google_id)
            
            # 1. Obtener el evento actual de Google
            existing_event = service.get(
                calendar_id='primary',
                event_id=self.google_id
            )
            
            # 2. Preparar datos de conferencia
            conference_data = {
                'createRequest': {
                    'conferenceSolutionKey': {'type': 'hangoutsMeet'},
                    'requestId': request_id,
                }
            }
            
            # 3. Si ya tiene conferencia, usar esa
            if existing_event.get('conferenceData'):
                conference_data = existing_event['conferenceData']
                _logger.info("Usando conferencia existente")
            
            # 4. Actualizar el evento
            body = {
                'conferenceData': conference_data
            }
            
            res = service.patch(
                calendar_id='primary',
                event_id=self.google_id,
                body=body,
                params={'conferenceDataVersion': 1},
                timeout=20
            )
            
            # 5. Extraer el enlace de Meet
            meet_link = res.get('hangoutLink', '')
            
            # 6. Si no está en hangoutLink, buscar en conferenceData
            if not meet_link:
                conference_data = res.get('conferenceData', {})
                entry_points = conference_data.get('entryPoints', [])
                
                for entry in entry_points:
                    if entry.get('entryPointType') == 'video':
                        meet_link = entry.get('uri', '')
                        break
            
            # 7. Si aún no se encuentra, buscar en la descripción
            if not meet_link:
                description = res.get('description', '')
                if 'meet.google.com' in description:
                    meet_link = description.split('meet.google.com')[0] + 'meet.google.com' + description.split('meet.google.com')[1].split()[0]
            
            if meet_link:
                _logger.info("Enlace Meet generado: %s", meet_link)
                return meet_link
            else:
                _logger.error("No se encontró enlace Meet en la respuesta: %s", json.dumps(res, indent=2))
                return False
            
        except Exception as e:
            _logger.error("Error creando Meet: %s", str(e), exc_info=True)
            return False

    def action_force_create_meet(self):
        self.ensure_one()

        # 1. Verificar conexión Google
        if not self.env.user.google_calendar_token:
            raise UserError(_("Configura tu conexión con Google Calendar primero"))
        
        # 2. Sincronizar si es necesario
        if not self.google_id:
            # Forzar sincronización inmediata
            self.with_context(sync_google_calendar=True).write({'need_sync': True})
            # Ejecutar sincronización de Odoo a Google
            self.env['calendar.event']._sync_odoo2google(self.env.user)
            # Esperar 5 segundos (puede ser necesario debido a demoras de Google)
            import time
            time.sleep(5)
            # Recargar el registro
            self.env.cache.invalidate()
            self = self.search([('id', '=', self.id)])
            if not self.google_id:
                raise UserError(_("No se pudo sincronizar con Google Calendar. Intenta nuevamente."))
        
        # 3. Crear Meet si no existe
        if not self.videocall_location:
            meet_link = self._create_google_meet()
            if meet_link:
                # Guardar directamente en la base de datos
                self.sudo().write({'videocall_location': meet_link})
                # Recargar vista
                return {
                    'type': 'ir.actions.client',
                    'tag': 'reload',
                }
            else:
                # Mostrar mensaje detallado
                error_msg = _(
                    "No se pudo generar el enlace de Meet. "
                    "Por favor verifica:\n"
                    "1. Que tienes permiso para crear reuniones de Google Meet\n"
                    "2. Que el evento está correctamente sincronizado con Google Calendar\n"
                    "3. Revisa los logs de Odoo para más detalles"
                )
                raise UserError(error_msg)
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': _("Enlace Meet generado: %s") % self.videocall_location,
                'type': 'success',
            }
        }

    @api.model
    def _sync_google_meet(self):
        """Sincronizar eventos que tienen Meet pero no enlace en Odoo"""
        try:
            # Solo procesar eventos de los últimos 7 días para eficiencia
            date_limit = fields.Datetime.now() - timedelta(days=7)
            
            events = self.search([
                ('google_id', '!=', False),
                ('is_google_meet', '=', True),
                ('videocall_location', '=', False),
                ('start', '>=', date_limit)
            ])
            
            _logger.info("Sincronizando %d eventos con Google Meet", len(events))
            
            service = GoogleCalendarService(self.env['google.service'])
            
            for event in events:
                try:
                    google_event = service.get(event.google_id, calendar_id='primary')
                    
                    # Extraer enlace Meet
                    meet_link = google_event.get('hangoutLink') or ''
                    if not meet_link and google_event.get('conferenceData'):
                        for entry_point in google_event['conferenceData'].get('entryPoints', []):
                            if entry_point.get('entryPointType') == 'video':
                                meet_link = entry_point.get('uri')
                                break
                    
                    if meet_link:
                        event.write({'videocall_location': meet_link})
                        _logger.info("Sincronizado Meet para evento %s: %s", event.name, meet_link)
                        # Pequeña pausa para evitar sobrecargar la API
                        time.sleep(0.5)
                        
                except Exception as e:
                    _logger.error("Error sincronizando Meet para evento %s: %s", event.name, str(e))
            
            return True
                    
        except Exception as e:
            _logger.error("Error general en sincronización de Meet: %s", str(e))
            return False