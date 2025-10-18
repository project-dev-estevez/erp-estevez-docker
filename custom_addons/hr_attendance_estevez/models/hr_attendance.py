from odoo import models, fields, api
from datetime import datetime
import logging
import pytz
        
_logger = logging.getLogger(__name__)

class HrAttendance(models.Model):
    
    _inherit = 'hr.attendance'

    department_id = fields.Many2one(
        'hr.department',
        string='Departamento',
        related='employee_id.department_id',
        store=True,
        readonly=True,
    )

    job_id = fields.Many2one(
        'hr.job',
        string='Puesto de trabajo',
        related='employee_id.job_id',
        store=True,
        readonly=True,
    )

    status = fields.Selection([
        ('pending', 'Pendiente'),
        ('retarded', 'Retardo'),
        ('approved', 'Aprobado'),
        ('rejected', 'Rechazado')], 
        string='Estado', 
        default='pending',
        tracking=True, 
        required=True
    )

    check_in_date = fields.Date(
        string='Fecha de Entrada',
        compute='_compute_check_dates',
        store=False
    )

    check_out_date = fields.Date(
        string='Fecha de Salida',
        compute='_compute_check_dates',
        store=False
    )

    is_auto_closed = fields.Boolean(
        string='Cerrado Automáticamente',
        help='Indica si la asistencia fue cerrada automáticamente por el sistema',
        default=False,
        tracking=True
    )

    check_out_display = fields.Char(string='Salida', compute='_compute_check_out_display')

    check_in_map_html = fields.Html(
        string='Mapa de Entrada',
        compute='_compute_check_in_map_html',
        sanitize=False
    )
    
    check_out_map_html = fields.Html(
        string='Mapa de Salida',
        compute='_compute_check_out_map_html',
        sanitize=False
    )

    has_admin_comments = fields.Boolean(
        string='Tiene comentarios del administrador',
        compute='_compute_has_admin_comments',
        store=False
    )

    @api.depends('message_ids', 'message_ids.body', 'message_ids.is_internal')
    def _compute_has_admin_comments(self):
        """
        Verifica si hay comentarios manuales del administrador.
        Excluye mensajes internos del sistema.
        """
        for record in self:
            # Filtrar mensajes que cumplan con estas condiciones:
            # 1. Tienen body (contenido)
            # 2. NO son internos (is_internal = False)
            # 3. Son de tipo notification o comment
            # 4. Tienen autor
            admin_messages = record.message_ids.filtered(
                lambda m: 
                    m.body and 
                    m.body.strip() not in ['', '<p><br></p>', '<p></p>', '<br>', '<br/>'] and
                    not m.is_internal and  # 🔑 CLAVE: Excluir mensajes internos
                    m.message_type in ['notification', 'comment'] and
                    m.author_id
            )
            
            record.has_admin_comments = len(admin_messages) > 0

    @api.depends('in_latitude', 'in_longitude')
    def _compute_check_in_map_html(self):
        for record in self:
            if record.in_latitude and record.in_longitude:
                lat, lng = record.in_latitude, record.in_longitude
                url = f"https://maps.google.com/maps?q={lat},{lng}&hl=es&z=16&output=embed"
                record.check_in_map_html = f"""
                    <div style="width: 100%; height: 360px; overflow: hidden;">
                        <iframe width="100%" height="360px" frameborder="0" style="border:0; display:block;"
                                src="{url}"
                                allowfullscreen></iframe>
                    </div>
                """
            else:
                record.check_in_map_html = "<p style='text-align:center; color:#999; width:100%; height:360px; display:flex; align-items:center; justify-content:center; border:1px dashed #ccc; margin:0;'>Sin ubicación GPS</p>"

    @api.depends('out_latitude', 'out_longitude')
    def _compute_check_out_map_html(self):
        for record in self:
            if record.out_latitude and record.out_longitude:
                lat, lng = record.out_latitude, record.out_longitude
                url = f"https://maps.google.com/maps?q={lat},{lng}&hl=es&z=16&output=embed"
                record.check_out_map_html = f"""
                    <div style="width: 100%; height: 360px; overflow: hidden;">
                        <iframe width="100%" height="360px" frameborder="0" style="border:0; display:block;"
                                src="{url}"
                                allowfullscreen></iframe>
                    </div>
                """
            else:
                record.check_out_map_html = "<p style='text-align:center; color:#999; width:100%; height:360px; display:flex; align-items:center; justify-content:center; border:1px dashed #ccc; margin:0;'>Sin ubicación GPS</p>"
    
    @api.depends('check_out', 'is_auto_closed')
    def _compute_check_out_display(self):
        for record in self:
            if record.is_auto_closed and not record.check_out:
                record.check_out_display = 'No Registró'
            elif record.check_out:
                # Obtener zona horaria del usuario actual o México por defecto
                user_tz = self.env.user.tz or 'America/Mexico_City'
                tz = pytz.timezone(user_tz)
                
                # Convertir de UTC a la zona horaria del usuario
                check_out_local = pytz.utc.localize(record.check_out).astimezone(tz)
                record.check_out_display = check_out_local.strftime('%d-%m-%Y %H:%M:%S')
            else:
                record.check_out_display = ''

    @api.depends('check_in', 'check_out')
    def _compute_check_dates(self):
        for record in self:
            record.check_in_date = record.check_in.date() if record.check_in else False
            record.check_out_date = record.check_out.date() if record.check_out else False

    @api.model
    def create(self, vals):
        check_in = vals.get('check_in')
        if check_in:
            try:
                if isinstance(check_in, str):
                    check_in_dt = datetime.strptime(check_in, '%Y-%m-%d %H:%M:%S')
                else:
                    check_in_dt = check_in
                if check_in_dt.hour > 8 or (check_in_dt.hour == 8 and check_in_dt.minute > 15):
                    vals['status'] = 'retarded'
                else:
                    vals['status'] = 'pending'
            except Exception:
                vals['status'] = 'pending'
        return super().create(vals)

    @api.model
    def auto_close_open_attendances(self):
        """
        🕚 CRONJOB: Cierra automáticamente todas las asistencias abiertas a las 11:58 PM
        Busca asistencias con check_in pero sin check_out y las cierra automáticamente
        """        
        try:
            # 🔍 Buscar asistencias abiertas (sin check_out)
            open_attendances = self.search([
                ('check_out', '=', False),
                ('check_in', '!=', False)
            ])
            
            if not open_attendances:
                _logger.info("🟢 No hay asistencias abiertas para cerrar")
                return True
            
            for attendance in open_attendances:
                try:                    
                    # ✅ Actualizar la asistencia
                    attendance.write({
                        'is_auto_closed': True,
                    })
                except Exception as e:
                    _logger.error(f"❌ Error cerrando asistencia ID {attendance.id}: {str(e)}")
                    continue
    
            return True
            
        except Exception as e:
            _logger.error(f"❌ Error en cronjob auto_close_open_attendances: {str(e)}")
            return False