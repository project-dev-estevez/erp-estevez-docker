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
            event.show_meet_button = (
                event.is_google_meet
                and not event.videocall_location
                and bool(event.google_id)
            )

    def _create_google_meet(self):
        """Parchea el evento en Google Calendar para crear Meet,
           guarda el enlace en videocall_location."""
        if not self.is_google_meet or self.videocall_location or not self.google_id:
            return False
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
            link = res.get('hangoutLink')
            if link:
                self.write({'videocall_location': link})
                _logger.info("Google Meet creado: %s", link)
                return link
        except Exception as e:
            _logger.exception("Error creando Google Meet: %s", e)
        return False

    def action_force_create_meet(self):
        """Botón: crea el Meet si ya existe google_id, sino informa error."""
        for event in self:
            if not event.google_id:
                raise UserError(_(
                    "El evento aún no se ha sincronizado con Google Calendar.\n"
                    "Guarda primero el evento y haz clic en 'Sincronizar calendario' "
                    "antes de generar el enlace."
                ))
            link = event._create_google_meet()
            if not link:
                raise UserError(_("No se pudo generar el enlace de Google Meet."))
        return {'type': 'ir.actions.client', 'tag': 'reload'}