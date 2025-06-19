from odoo import models, api, fields
import uuid

class CalendarEvent(models.Model):
    _inherit = 'calendar.event'
    
    # Campo adicional para controlar el tipo de meet
    is_google_meet = fields.Boolean(string="Usar Google Meet", default=True)
    
    # Sobrescribir creación para evitar meet de Odoo
    @api.model_create_multi
    def create(self, vals_list):
        # Desactivar videollamada automática de Odoo
        for vals in vals_list:
            if 'videocall_location' not in vals:
                vals['videocall_location'] = False
        return super().create(vals_list)
    
    # Método modificado para Google Meet
    def _google_values(self):
        values = super()._google_values()
        
        # Solo si está marcado para Google Meet
        if self.is_google_meet and not self.videocall_location:
            values['conferenceData'] = {
                'createRequest': {
                    'conferenceSolutionKey': {'type': 'hangoutsMeet'},
                    'requestId': str(uuid.uuid4()),
                }
            }
        return values