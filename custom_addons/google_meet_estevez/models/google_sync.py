from odoo import models

class GoogleCalendarSync(models.AbstractModel):
    _inherit = 'google.calendar.sync'

    def _import_event(self, event):
        values = super()._import_event(event)
        
        # Extraer enlace Meet
        meet_link = event.get('hangoutLink') or ''
        if not meet_link and event.get('conferenceData'):
            for entry_point in event['conferenceData'].get('entryPoints', []):
                if entry_point.get('entryPointType') == 'video':
                    meet_link = entry_point.get('uri')
                    break

        if meet_link:
            values['videocall_location'] = meet_link
            
        return values