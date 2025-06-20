from odoo import models, fields, api, _
from odoo.exceptions import UserError
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
    
    # 1. Desactivar completamente las videollamadas de Odoo
    @api.model
    def _init_videocall(self):
        return False  # Desactiva completamente la generación de videollamadas de Odoo
    
    # 2. Método para crear Google Meet
    def _create_google_meet(self):
        if not self.is_google_meet or self.videocall_location or not self.google_id:
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
    
    # 3. Sincronización con Google Calendar
    def _sync_odoo2google(self, google_service):
        res = super()._sync_odoo2google(google_service)
        if self.is_google_meet and self.google_id:
            # Esperar 5 segundos para que Google procese
            self.env.cr.commit()
            import time
            time.sleep(5)
            self._create_google_meet()
        return res
    
    # 4. Método manual para generación
    def force_create_meet(self):
        for record in self:
            if not record.google_id:
                raise UserError(_("Primero sincroniza el evento con Google Calendar"))
            record._create_google_meet()
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Google Meet'),
                    'message': _('Enlace Meet generado exitosamente'),
                    'sticky': False,
                }
            }