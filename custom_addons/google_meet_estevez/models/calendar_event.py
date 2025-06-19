from odoo import models, api
import uuid

class CalendarEvent(models.Model):
    _inherit = 'calendar.event'

    @api.model
    def _google_values(self):
        """Sobrescribe los valores enviados a Google para incluir Meet"""
        values = super()._google_values()
        
        # Solo crea Meet si no hay enlace existente
        if not self.videocall_location:
            values['conferenceData'] = {
                'createRequest': {
                    'conferenceSolutionKey': {'type': 'hangoutsMeet'},
                    'requestId': str(uuid.uuid4()),  # ID único requerido
                }
            }
        return values
    
    # Parche dinámico para agregar el scope (Odoo 18)
    from odoo.addons.google_calendar.models.google_sync import GoogleCalendarService
    GoogleCalendarService.SCOPES = GoogleCalendarService.SCOPES + [
        'https://www.googleapis.com/auth/meetings.space.created'
    ]