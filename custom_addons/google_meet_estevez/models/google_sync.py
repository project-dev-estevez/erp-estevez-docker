# models/google_sync.py
from odoo import models
from odoo.addons.google_calendar.models.google_sync import GoogleSync

class CustomGoogleSync(GoogleSync):
    _inherit = 'google.sync'

    def _import_event(self, event):
        values = super()._import_event(event)
        
        # Extraer enlace Meet de la respuesta de Google
        meet_link = event.get('hangoutLink') or ''
        if not meet_link and event.get('conferenceData'):
            for entry_point in event['conferenceData'].get('entryPoints', []):
                if entry_point.get('entryPointType') == 'video':
                    meet_link = entry_point.get('uri')
                    break

        if meet_link:
            values['videocall_location'] = meet_link
            
        return values