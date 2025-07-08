from odoo import models, fields, api, _
from odoo.exceptions import UserError
import uuid
import logging
import time
from odoo.addons.google_calendar.utils.google_calendar import GoogleCalendarService


_logger = logging.getLogger(__name__)

class CalendarEvent(models.Model):
    _inherit = 'calendar.event'

    # Mantener campos existentes
    is_google_meet = fields.Boolean(
        string="Usar Google Meet",
        default=True
    )

    # Campo computado para control de visibilidad
    show_meet_button = fields.Boolean(
        string="Mostrar botón Meet",
        compute="_compute_show_meet_button",
        store=True
    )

    @api.depends('is_google_meet', 'videocall_location', 'google_id')
    def _compute_show_meet_button(self):
        for event in self:
            event.show_meet_button = (
                event.is_google_meet and 
                not event.videocall_location and
                bool(event.google_id)
            )


    # Método mejorado para crear Google Meet
    def _create_google_meet(self):
        if not self.is_google_meet or self.videocall_location or not self.google_id:

            return False
            
        service = GoogleCalendarService(self.env['google.service'])
        event_data = {

            'conferenceData': {
                'createRequest': {
                    'conferenceSolutionKey': {'type': 'hangoutsMeet'},
                    'requestId': str(uuid.uuid4()),
                }
            }
        }
        
        try:
            result = service.patch(
                calendar_id='primary',
                event_id=self.google_id,
                body=event_data,
                params={'conferenceDataVersion': 1}
            )
            meet_url = result.get('hangoutLink')
            if meet_url:
                self.write({'videocall_location': meet_url})
                _logger.info("Google Meet creado: %s", meet_url)
                return meet_url
        except Exception as e:
            _logger.exception("Error creando Google Meet: %s", str(e))
        return False
    
    # Método mejorado para forzar sincronización
    def _force_sync_to_google(self):
        """Forzar sincronización inmediata con Google Calendar"""
        try:
            # Sincronizar usando el método interno de Google Calendar
            service = self.env['google.calendar.service'].google_service()
            GoogleCalendarSynchronization.sync_events(self.env, self)
            
            # Esperar y recargar
            self.env.cr.commit()
            time.sleep(5)
            self.env.invalidate_all()
            return self.search([('id', '=', self.id)])
        except Exception as e:
            _logger.error("Error sincronizando evento: %s", str(e))
            return self

    # Método manual mejorado
    def force_create_meet(self):
        for event in self:
            # Si no tiene google_id, forzar sincronización primero
            if not event.google_id:
                event = event._force_sync_to_google()
                
                # Si después de sincronizar sigue sin google_id
                if not event.google_id:
                    raise UserError(_(
                        "No se pudo sincronizar con Google Calendar. "
                        "Verifica: \n"
                        "1. Que el calendario esté configurado para sincronizar\n"
                        "2. Que tengas conexión a internet\n"
                        "3. Que la integración con Google esté activa"
                    ))
            
            # Crear Meet
            meet_url = event._create_google_meet()
            if meet_url:
                # Recargar la vista
                return {
                    'type': 'ir.actions.client',
                    'tag': 'reload',
                }
            else:
                raise UserError(_("Error generando Google Meet. Ver logs para más detalles."))
    
    # Sincronización automática mejorada
    def _sync_odoo2google(self, google_service):
        res = super()._sync_odoo2google(google_service)
        if self.is_google_meet and self.google_id and not self.videocall_location:
            # Intentar crear Meet después de sincronizar
            self._create_google_meet()
        return res

    def _compute_show_meet_button(self):
        for event in self:
            event.show_meet_button = (
                event.is_google_meet and 
                not event.videocall_location and
                event.google_id
            )

