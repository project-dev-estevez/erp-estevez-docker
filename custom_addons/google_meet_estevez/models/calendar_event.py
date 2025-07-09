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
    )
    show_meet_button = fields.Boolean(
        string="Mostrar botón Meet",
        compute="_compute_show_meet_button",
        store=True,
    )

    @api.depends('is_google_meet', 'videocall_location', 'google_id')
    def _compute_show_meet_button(self):
        for event in self:
            # Condición simplificada para mejor rendimiento
            event.show_meet_button = (
                event.is_google_meet and 
                not event.videocall_location and 
                bool(event.google_id)
            )

    def _create_google_meet(self):
        """Crea una reunión de Google Meet"""
        service = GoogleCalendarService(self.env['google.service'])
        try:
            res = service.patch(
                calendar_id='primary',
                event_id=self.google_id,
                body={
                    'conferenceData': {
                        'createRequest': {
                            'conferenceSolutionKey': {'type': 'hangoutsMeet'},
                            'requestId': str(uuid.uuid4()),
                        }
                    }
                },
                params={'conferenceDataVersion': 1},
            )
            return res.get('hangoutLink')
        except Exception as e:
            _logger.error("Error creando Google Meet: %s", e)
            return False

    def action_force_create_meet(self):
        self.ensure_one()

        # Verificar conexión con Google
        if not self.env.user.google_calendar_token:
            raise UserError(_("Primero debes configurar tu conexión con Google Calendar"))

        # Si no tiene ID de Google, sincronizar primero
        if not self.google_id:
            try:
                # Forzar sincronización
                self.need_sync = True
                
                # Ejecutar la sincronización para este evento
                self.env['calendar.event']._sync_odoo2google(self.env.user)
                
                # Recargar datos manualmente
                self.env.cache.invalidate()
                self = self.search([('id', '=', self.id)], limit=1)
                
                if not self.google_id:
                    raise UserError(_("No se pudo sincronizar el evento con Google Calendar. Por favor, guarda el evento e inténtalo de nuevo."))
            except Exception as e:
                raise UserError(_("Error al sincronizar con Google: %s") % str(e))

        # Crear Meet si no existe
        if not self.videocall_location:
            meet_link = self._create_google_meet()
            if not meet_link:
                raise UserError(_("No se pudo generar el enlace de Google Meet"))
            
            self.videocall_location = meet_link

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _("Google Meet generado"),
                'message': _("Enlace creado: %s") % self.videocall_location,
                'type': 'success',
                'sticky': False,
                'next': {
                    'type': 'ir.actions.act_window',
                    'res_model': 'calendar.event',
                    'res_id': self.id,
                    'views': [(False, 'form')],
                    'target': 'current',
                }
            }
        }