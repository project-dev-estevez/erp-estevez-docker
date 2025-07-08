from odoo import models, fields, api, _
from odoo.exceptions import UserError
import uuid
import logging
import time
from odoo.addons.google_calendar.utils.google_calendar import GoogleCalendarService
from odoo.addons.google_calendar.models.google_calendar import GoogleCalendarSynchronization

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
        self.ensure_one()
        if not self.is_google_meet or self.videocall_location:
            return False
        # Servicio bien inicializado
        service_account = self.env['google.service'].search([], limit=1)
        service = GoogleCalendarService(service_account)
        body = {
            'conferenceData': {
                'createRequest': {
                    'conferenceSolutionKey': {'type': 'hangoutsMeet'},
                    'requestId': str(uuid.uuid4()),
                }
            }
        }
        result = service.patch(
            calendar_id='primary',
            event_id=self.google_id,
            body=body,
            params={'conferenceDataVersion': 1}
        )
        link = result.get('conferenceData', {}).get('entryPoints', [])
        # Google devuelve entryPoints; busca el tipo 'video'
        for ep in link:
            if ep.get('entryPointType') == 'video':
                url = ep.get('uri')
                self.videocall_location = url
                return url
        return False

    # Método mejorado para forzar sincronización
    def _force_sync_to_google(self):
        """ Forzar sincronización inmediatamente """
        for event in self:
            GoogleCalendarSynchronization(service_account).sync_events(self.env, self)
        # No necesitas sleep/commit; el ORM lo refresca en la vista
        return True
    
    # Método manual mejorado
    def force_create_meet(self):
        for event in self:
            if not event.google_id:
                # Sincroniza primero
                if not event._force_sync_to_google():
                    raise UserError(_("No se pudo sincronizar con Google Calendar."))
            # Crea Meet
            meet_url = event._create_google_meet()
            if not meet_url:
                raise UserError(_("Error generando Google Meet. Revisa los logs."))
        # Después de procesar todos, recarga el form
        return {'type': 'ir.actions.client', 'tag': 'reload'}
        
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
    
    show_meet_button = fields.Boolean(
        compute="_compute_show_meet_button",
        string="Mostrar botón Meet"
    )