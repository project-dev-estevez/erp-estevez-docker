from odoo import models, fields, api
import uuid
import logging
from odoo.addons.google_calendar.utils.google_calendar import GoogleCalendarService

_logger = logging.getLogger(__name__)

class CalendarEvent(models.Model):
    _inherit = 'calendar.event'
    
    is_google_meet = fields.Boolean(
        string="Usar Google Meet",
        default=True,
        help="Genera un enlace de Google Meet al sincronizar"
    )
    
    # Método clave para forzar la generación de Meet
    def _create_google_meet(self):
        if not self.is_google_meet or self.videocall_location:
            return
            
        service = GoogleCalendarService(self.env['google.service'])
        event = {
            'conferenceData': {
                'createRequest': {
                    'conferenceSolutionKey': {'type': 'hangoutsMeet'},
                    'requestId': str(uuid.uuid4()),
                }
            }
        }
        
        try:
            # Forzar creación de Meet
            result = service.patch(
                calendar_id='primary',
                event_id=self.google_id,
                body=event,
                params={'conferenceDataVersion': 1}
            )
            meet_url = result.get('hangoutLink')
            if meet_url:
                self.write({'videocall_location': meet_url})
                _logger.info("Google Meet creado: %s", meet_url)
            else:
                _logger.error("Google no devolvió enlace Meet")
        except Exception as e:
            _logger.exception("Error creando Google Meet: %s", str(e))

    # Ejecutar después de sincronizar
    def _sync_odoo2google(self, google_service):
        res = super()._sync_odoo2google(google_service)
        if self.is_google_meet and self.google_id:
            # Esperar 10 segundos para que Google procese
            self.env.cr.commit()
            import time
            time.sleep(10)
            self._create_google_meet()
        return res
    
    def force_create_meet(self):
        """
        Método para forzar la creación de un enlace Meet manualmente
        """
        for record in self:
            if not record.google_id:
                raise UserError(_("Primero sincroniza el evento con Google Calendar"))
            
            # Llamamos al método que crea el Meet
            record._create_google_meet()
            
            # Mostramos mensaje de confirmación
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Google Meet'),
                    'message': _('Enlace Meet generado exitosamente'),
                    'sticky': False,
                }
            }