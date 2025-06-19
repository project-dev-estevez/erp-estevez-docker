from odoo import models, fields, api
import uuid

class CalendarEvent(models.Model):
    _inherit = 'calendar.event'
    
    
    is_google_meet = fields.Boolean(
        string="Usar Google Meet",
        default=True,
        help="Genera un enlace de Google Meet al sincronizar"
    )
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'videocall_location' not in vals:
                vals['videocall_location'] = False
        return super().create(vals_list)
    
    def _google_values(self):
        values = super()._google_values()
        if self.is_google_meet and not self.videocall_location:
            values['conferenceData'] = {
                'createRequest': {
                    'conferenceSolutionKey': {'type': 'hangoutsMeet'},
                    'requestId': str(uuid.uuid4()),
                }
            }
        return values