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

        if not self.google_id:
            # Obtener la tabla real del modelo
            table = self.env['google.service']._table

            # Ejecutar SQL para obtener el ID del primer registro (configuración de Google)
            self.env.cr.execute(f"SELECT id FROM {table} LIMIT 1")
            row = self.env.cr.fetchone()

            if not row:
                raise UserError(_("No hay ninguna configuración activa para Google Calendar."))

            # Obtener el registro de configuración
            config = self.env['google.service'].sudo().browse(row[0])

            # Sincronizar el evento con Google Calendar
            try:
                super(type(self), self)._sync_odoo2google(config.google_service())
            except Exception as e:
                raise UserError(_("Error al sincronizar con Google Calendar: %s") % str(e))

        # Mostrar el mensaje con el enlace Meet
        if not self.google_meet_url:
            raise UserError(_("No se pudo generar el enlace de Google Meet."))

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _("Google Meet generado"),
                'message': _("Enlace: <a href='%s' target='_blank'>%s</a>") % (
                    self.google_meet_url, self.google_meet_url),
                'type': 'success',
                'sticky': False,
            }
        }