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
        self.ensure_one()

        # 1) Sincronizar si falta google_id
        if not self.google_id:
            config = self.env['google.service'].sudo().search([], limit=1, order='')
            if not config:
                raise UserError(_("Falta configurar Google Calendar (google.service)."))
            try:
                super(CalendarEvent, self)._sync_odoo2google(config.google_service())
                self.invalidate_cache(['google_id'])
            except Exception as e:
                _logger.exception("Error sincronizando con Google: %s", e)
                raise UserError(_(
                    "No se pudo sincronizar con Google Calendar.\n"
                    "Revisa la configuración y los logs."
                ))
            if not self.google_id:
                raise UserError(_(
                    "Tras sincronizar, el evento aún no tiene ID en Google."
                ))

        # 2) Crear Meet
        url = self._create_google_meet()
        if not url:
            raise UserError(_("No se pudo generar el enlace de Google Meet."))
        return {'type': 'ir.actions.client', 'tag': 'reload'}