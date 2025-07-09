from odoo import models, fields, api, _
from odoo.exceptions import UserError
import uuid
import logging
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

    @api.depends('is_google_meet', 'videocall_location', 'google_id')
    def _compute_show_meet_button(self):
        for event in self:
            event.show_meet_button = (
                event.is_google_meet
                and not event.videocall_location
                and bool(event.google_id)
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

    def _ensure_event_is_syncable(self):
        """Verifica que el evento tenga los datos mínimos para sincronizar"""
        if not self.start or not self.stop:
            raise UserError(_("El evento debe tener fecha de inicio y fin"))
        if not self.name:
            raise UserError(_("El evento debe tener un título"))
        if not self.user_id or not self.user_id.email:
            raise UserError(_("El organizador debe tener un email válido"))

    def action_force_create_meet(self):
        self.ensure_one()

        # Verificar conexión con Google
        if not self.env.user.google_calendar_token:
            raise UserError(_("Primero debes configurar tu conexión con Google Calendar"))

        # Verificar que el evento sea sincronizable
        self._ensure_event_is_syncable()

        # Si no tiene ID de Google, sincronizar primero
        if not self.google_id:
            try:
                # Forzar sincronización
                self.write({'need_sync': True})
                
                # Crear un diccionario con los datos del evento
                event_data = {
                    'start': self.start,
                    'stop': self.stop,
                    'name': self.name,
                    'description': self.description,
                    'location': self.location,
                    'partner_ids': [(6, 0, self.partner_ids.ids)],
                    'user_id': self.user_id.id,
                    'allday': self.allday,
                    'show_as': self.show_as,
                    'privacy': self.privacy,
                    'need_sync': True,
                }
                
                # Crear un evento temporal para sincronizar
                temp_event = self.env['calendar.event'].create(event_data)
                temp_event.with_context(no_mail_to_attendees=True)._sync_google_calendar()
                
                # Si se creó correctamente, copiar el google_id
                if temp_event.google_id:
                    self.google_id = temp_event.google_id
                    # Eliminar el evento temporal
                    temp_event.unlink()
                else:
                    raise UserError(_("No se pudo sincronizar el evento con Google Calendar"))
                
            except Exception as e:
                _logger.exception("Error sincronizando evento: %s", str(e))
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