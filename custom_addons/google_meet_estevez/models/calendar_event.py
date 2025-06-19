from odoo import models, fields, api
import uuid
import logging

_logger = logging.getLogger(__name__)

class CalendarEvent(models.Model):
    _inherit = 'calendar.event'
    
    is_google_meet = fields.Boolean(
        string="Usar Google Meet",
        default=True,
        help="Genera un enlace de Google Meet al sincronizar"
    )
    
    # Desactivar completamente las videollamadas de Odoo
    def _init_videocall(self):
        if self.is_google_meet:
            self.videocall_location = False
            return
        return super()._init_videocall()
    
    # Método modificado para Google Meet
    def _google_values(self):
        values = super()._google_values()
        
        # Solo si está marcado para Google Meet y no tiene enlace
        if self.is_google_meet and not self.videocall_location:
            # Forzar desactivación de videollamada de Odoo
            values['videocall_location'] = False
            
            # Generar Meet de Google
            values['conferenceData'] = {
                'createRequest': {
                    'conferenceSolutionKey': {'type': 'hangoutsMeet'},
                    'requestId': str(uuid.uuid4()),
                }
            }
            _logger.info("Google Meet requested for event %s", self.id)
        return values
    
    # Forzar actualización después de sincronizar
    def _sync_odoo2google(self, google_service):
        res = super()._sync_odoo2google(google_service)
        if self.is_google_meet and self.google_id:
            # Recargar evento para obtener Meet URL
            self.env.cr.commit()
            self.env['calendar.event'].search([('id', '=', self.id)]).write({})
        return res