from odoo import models, fields, api, _
from odoo.exceptions import UserError
import uuid
import logging
from odoo.addons.google_calendar.utils.google_calendar import GoogleCalendarService
from odoo.addons.google_calendar.models.google_sync import GoogleSync

_logger = logging.getLogger(__name__)

class CalendarEvent(models.Model):
    _inherit = 'calendar.event'

    # ... (otros campos y métodos)

    def action_force_create_meet(self):
        self.ensure_one()

        # Verificar conexión con Google
        if not self.env.user.google_calendar_token:
            raise UserError(_("Primero debes configurar tu conexión con Google Calendar"))
        
        # Verificar que el evento tenga los datos mínimos
        if not self.start or not self.stop:
            raise UserError(_("El evento debe tener fecha de inicio y fin"))
        if not self.name:
            raise UserError(_("El evento debe tener un título"))

        # Si no tiene ID de Google, sincronizar primero
        if not self.google_id:
            try:
                # Actualizar el estado de sincronización
                self.write({'need_sync': True})
                
                # Ejecutar la sincronización manualmente
                GoogleSync(self.env['google.service']).sync_events(
                    self.env.user, 
                    events=self,
                    timeout=10  # Tiempo de espera en segundos
                )
                
                # Recargar los datos del evento
                self.env.cache.invalidate()
                self = self.search([('id', '=', self.id)], limit=1)
                
                if not self.google_id:
                    # Intento alternativo si falla la sincronización normal
                    _logger.warning("Sincronización normal fallida, intentando método alternativo")
                    self.with_delay()._sync_google_calendar()
                    self.env.cache.invalidate()
                    self = self.search([('id', '=', self.id)], limit=1)
                    
                    if not self.google_id:
                        raise UserError(_("No se pudo sincronizar el evento con Google Calendar. Por favor, verifica tu conexión o intenta más tarde."))
                    
            except Exception as e:
                _logger.error("Error sincronizando evento: %s", str(e))
                raise UserError(_("Error al sincronizar con Google: %s") % str(e))

        # Crear Meet si no existe
        if not self.videocall_location:
            meet_link = self._create_google_meet()
            if not meet_link:
                raise UserError(_("No se pudo generar el enlace de Google Meet. Por favor, inténtalo de nuevo."))
            
            self.write({'videocall_location': meet_link})

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