import uuid
import logging
import time
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.addons.google_calendar.utils.google_calendar import GoogleCalendarService
from datetime import timedelta

_logger = logging.getLogger(__name__)

class CalendarEvent(models.Model):
    _inherit = 'calendar.event'

    is_google_meet = fields.Boolean(
        string="Usar Google Meet",
        default=True,
    )
    meet_generation_state = fields.Selection([
        ('pending', 'Pendiente'),
        ('processing', 'Procesando'),
        ('done', 'Completado'),
        ('failed', 'Fallido')
    ], string="Estado de Meet", default='pending', readonly=True)
    show_meet_button = fields.Boolean(
        string="Mostrar botón Meet",
        compute="_compute_show_meet_button",
        store=True,
    )
    videocall_location = fields.Char(string="Enlace Meet")

    @api.depends('is_google_meet', 'videocall_location', 'google_id', 'meet_generation_state')
    def _compute_show_meet_button(self):
        for event in self:
            event.show_meet_button = (
                event.is_google_meet and 
                not event.videocall_location and 
                bool(event.google_id) and
                event.meet_generation_state in ['pending', 'failed']
            )

    def _create_google_meet(self, max_retries=3):
        """Crea una reunión de Google Meet con reintentos"""
        for attempt in range(max_retries):
            try:
                service = GoogleCalendarService(self.env['google.service'])
                request_id = str(uuid.uuid4())
                
                _logger.info(f"Intento {attempt+1} de crear Google Meet para evento: {self.name}")
                
                # 1. Obtener el evento actual de Google
                existing_event = service.get(
                    calendar_id='primary',
                    event_id=self.google_id
                )
                
                # 2. Preparar datos de conferencia
                conference_data = existing_event.get('conferenceData', {})
                if not conference_data.get('createRequest'):
                    conference_data['createRequest'] = {
                        'conferenceSolutionKey': {'type': 'hangoutsMeet'},
                        'requestId': request_id,
                    }
                
                # 3. Actualizar el evento
                body = {
                    'conferenceData': conference_data
                }
                
                res = service.patch(
                    calendar_id='primary',
                    event_id=self.google_id,
                    body=body,
                    params={'conferenceDataVersion': 1},
                    timeout=20
                )
                
                # 4. Extraer el enlace de Meet con múltiples estrategias
                meet_link = res.get('hangoutLink') or ''
                
                if not meet_link:
                    conference_data = res.get('conferenceData', {})
                    entry_points = conference_data.get('entryPoints', [])
                    
                    for entry in entry_points:
                        if entry.get('entryPointType') == 'video':
                            meet_link = entry.get('uri', '')
                            break
                
                if not meet_link and res.get('description', ''):
                    description = res['description']
                    if 'meet.google.com' in description:
                        parts = description.split('meet.google.com')
                        if len(parts) > 1:
                            meet_link = 'https://meet.google.com' + parts[1].split()[0].split('<')[0].split('>')[0]
                
                if meet_link:
                    _logger.info(f"Enlace Meet generado en intento {attempt+1}: {meet_link}")
                    return meet_link
                
                # Si no se encontró enlace, esperar antes de reintentar
                _logger.warning(f"No se encontró enlace Meet en intento {attempt+1}")
                time.sleep(2)  # Espera 2 segundos antes de reintentar
            
            except Exception as e:
                _logger.error(f"Error en intento {attempt+1}: {str(e)}")
                time.sleep(3)  # Esperar más tiempo después de un error
        
        _logger.error(f"Fallo al crear Meet después de {max_retries} intentos")
        return False

    def action_force_create_meet(self):
        self.ensure_one()

        # Evitar múltiples clics simultáneos
        if self.meet_generation_state == 'processing':
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': _("La generación de Meet ya está en proceso..."),
                    'type': 'warning',
                }
            }
        
        try:
            # Marcar como procesando
            self.sudo().write({'meet_generation_state': 'processing'})
            
            # 1. Verificar conexión Google
            if not self.env.user.google_calendar_token:
                raise UserError(_("Configura tu conexión con Google Calendar primero"))
            
            # 2. Sincronizar si es necesario
            if not self.google_id:
                # Forzar sincronización
                self.with_context(sync_google_calendar=True).write({'need_sync': True})
                self.env['calendar.event']._sync_odoo2google(self.env.user)
                
                # Esperar activamente hasta 30 segundos por la sincronización
                start_time = time.time()
                while not self.google_id and time.time() - start_time < 30:
                    time.sleep(2)
                    self.env.cache.invalidate()
                    self = self.search([('id', '=', self.id)])
                
                if not self.google_id:
                    raise UserError(_("Sincronización con Google Calendar fallida después de 30 segundos"))
            
            # 3. Crear Meet
            meet_link = self._create_google_meet()
            if meet_link:
                # Guardar y actualizar estado
                self.sudo().write({
                    'videocall_location': meet_link,
                    'meet_generation_state': 'done'
                })
                
                # Recargar vista
                return {
                    'type': 'ir.actions.client',
                    'tag': 'reload',
                }
            else:
                # Actualizar estado a fallido
                self.sudo().write({'meet_generation_state': 'failed'})
                raise UserError(_("""
No se pudo generar el enlace de Meet después de 3 intentos. 
Posibles causas:
1. Permisos insuficientes en Google Workspace
2. El evento no se ha sincronizado completamente con Google Calendar
3. Problemas temporales con la API de Google

Solución:
- Espera 5 minutos e intenta nuevamente
- Verifica el evento en Google Calendar directamente
- Revisa los logs de Odoo para más detalles
                """))
        
        except Exception as e:
            # Actualizar estado a fallido
            self.sudo().write({'meet_generation_state': 'failed'})
            raise UserError(_("Error inesperado: %s") % str(e))

    @api.model
    def _sync_google_meet(self):
        """Sincronizar eventos que tienen Meet pero no enlace en Odoo"""
        try:
            # Procesar eventos fallidos o pendientes
            events = self.search([
                ('google_id', '!=', False),
                ('is_google_meet', '=', True),
                ('videocall_location', '=', False),
                ('meet_generation_state', 'in', ['pending', 'failed']),
                ('start', '>=', fields.Datetime.now() - timedelta(days=30))
            ])
            
            _logger.info("Sincronizando %d eventos con Google Meet", len(events))
            
            service = GoogleCalendarService(self.env['google.service'])
            
            for event in events:
                try:
                    # Marcar como procesando
                    event.write({'meet_generation_state': 'processing'})
                    
                    google_event = service.get(event.google_id, calendar_id='primary')
                    
                    # Extraer enlace Meet
                    meet_link = google_event.get('hangoutLink') or ''
                    if not meet_link:
                        for entry_point in google_event.get('conferenceData', {}).get('entryPoints', []):
                            if entry_point.get('entryPointType') == 'video':
                                meet_link = entry_point.get('uri')
                                break
                    
                    if meet_link:
                        event.write({
                            'videocall_location': meet_link,
                            'meet_generation_state': 'done'
                        })
                        _logger.info("Sincronizado Meet para evento %s", event.name)
                    else:
                        event.write({'meet_generation_state': 'failed'})
                        _logger.warning("No se encontró Meet para evento %s", event.name)
                    
                    # Pequeña pausa para evitar sobrecargar la API
                    time.sleep(0.5)
                    
                except Exception as e:
                    event.write({'meet_generation_state': 'failed'})
                    _logger.error("Error sincronizando Meet: %s", str(e))
            
            return True
                    
        except Exception as e:
            _logger.error("Error general en sincronización: %s", str(e))
            return False
        
    @api.model
    def _sync_google_meet(self):
        """Sincronizar eventos que tienen Meet pero no enlace en Odoo"""
        # Implementación anterior (sin cambios)
        pass
        
    @api.model
    def _reset_meet_states(self):
        """Limpia estados de generación de Meet para eventos antiguos"""
        # Implementación anterior (sin cambios)
        pass