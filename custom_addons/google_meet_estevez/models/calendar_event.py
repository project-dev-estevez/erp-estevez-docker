import uuid
import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.addons.google_calendar.utils.google_calendar import GoogleCalendarService
from odoo.addons.google_calendar.models.google_sync import GoogleSync

_logger = logging.getLogger(__name__)

class CalendarEvent(models.Model):
    _inherit = 'calendar.event'

    is_google_meet = fields.Boolean(
        string="Usar Google Meet",
        default=True,
    )
    show_meet_button = fields.Boolean(
        string="Mostrar botón Meet",
        compute="_compute_show_meet_button",
        store=True,
    )
    videocall_location = fields.Char(string="Enlace Meet")  # Asegúrate de tener este campo

    @api.depends('is_google_meet', 'videocall_location', 'google_id')
    def _compute_show_meet_button(self):
        for event in self:
            event.show_meet_button = (
                event.is_google_meet and 
                not event.videocall_location and 
                bool(event.google_id)
            )

    def _create_google_meet(self):
        """Crea una reunión de Google Meet con los nuevos permisos"""
        try:
            service = GoogleCalendarService(self.env['google.service'])
            request_id = str(uuid.uuid4())
            
            _logger.info("Creando Google Meet para evento: %s", self.name)
            
            body = {
                'conferenceData': {
                    'createRequest': {
                        'conferenceSolutionKey': {'type': 'hangoutsMeet'},
                        'requestId': request_id,
                    }
                }
            }
            
            res = service.patch(
                calendar_id='primary',
                event_id=self.google_id,
                body=body,
                params={'conferenceDataVersion': 1},
                timeout=15
            )
            
            # Extraer el enlace de Meet
            meet_link = res.get('hangoutLink') or ''
            if not meet_link and res.get('conferenceData'):
                for entry_point in res['conferenceData'].get('entryPoints', []):
                    if entry_point.get('entryPointType') == 'video':
                        meet_link = entry_point.get('uri')
                        break
            
            return meet_link
            
        except Exception as e:
            _logger.error("Error creando Meet: %s", str(e))
            return False

    def action_force_create_meet(self):
        self.ensure_one()

        # 1. Verificar conexión Google
        if not self.env.user.google_calendar_token:
            raise UserError(_("Configura tu conexión con Google Calendar primero"))
        
        # 2. Sincronizar si es necesario
        if not self.google_id:
            # Usar la sincronización nativa de Odoo
            self.with_context(sync_google_calendar=True).write({
                'need_sync': True
            })
            self.env['calendar.event']._sync_google2odoo(self.env.user)
            self.env.cache.invalidate()
            self = self.search([('id', '=', self.id)])
            if not self.google_id:
                raise UserError(_("No se pudo sincronizar con Google Calendar. Intenta nuevamente."))
        
        # 3. Crear Meet si no existe
        if not self.videocall_location:
            meet_link = self._create_google_meet()
            if meet_link:
                # Guardar directamente en la base de datos
                self.sudo().write({'videocall_location': meet_link})
                # Recargar vista
                return {
                    'type': 'ir.actions.client',
                    'tag': 'reload',
                }
            else:
                raise UserError(_("No se pudo generar el enlace de Meet. Intenta nuevamente."))
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': _("Enlace Meet generado: %s") % self.videocall_location,
                'type': 'success',
            }
        }
    
    @api.model
    def _sync_google_meet(self):
        """Sincronizar eventos que tienen Meet pero no enlace en Odoo"""
        events = self.search([
            ('google_id', '!=', False),
            ('is_google_meet', '=', True),
            ('videocall_location', '=', False)
        ])
        
        for event in events:
            try:
                service = GoogleCalendarService(self.env['google.service'])
                google_event = service.get(event.google_id, calendar_id='primary')
                
                # Extraer enlace Meet
                meet_link = google_event.get('hangoutLink') or ''
                if not meet_link and google_event.get('conferenceData'):
                    for entry_point in google_event['conferenceData'].get('entryPoints', []):
                        if entry_point.get('entryPointType') == 'video':
                            meet_link = entry_point.get('uri')
                            break
                
                if meet_link:
                    event.videocall_location = meet_link
                    _logger.info("Sincronizado Meet para evento %s: %s", event.name, meet_link)
                    
            except Exception as e:
                _logger.error("Error sincronizando Meet para evento %s: %s", event.name, str(e))

    def write(self, vals):
        # Registrar cambios para depuración
        if 'videocall_location' in vals:
            _logger.info("Actualizando videocall_location: %s", vals['videocall_location'])
        return super().write(vals)