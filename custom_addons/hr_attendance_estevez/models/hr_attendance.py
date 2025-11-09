from odoo import models, fields, api
from datetime import datetime
import logging
        
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
        ('approved', 'Aprobado'),
        ('rejected', 'Rechazado')], 
        string='Estado', 
        default='pending',
        tracking=True, 
        required=True
    )

    tag_ids = fields.Many2many(
        'hr.attendance.tag',
        'hr_attendance_tag_rel',
        'attendance_id',
        'tag_id',
        string='Etiquetas',
        help='Etiquetas asociadas a la asistencia.'
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
    
    @api.depends('check_out', 'is_auto_closed', 'check_in')
    def _compute_check_out_display(self):
        for record in self:
            # Mostrar "No Registró" si es cierre automático y check_in == check_out o check_out vacío
            if record.is_auto_closed and (not record.check_out or record.check_in == record.check_out):
                record.check_out_display = 'No Registró'
            elif record.check_out:
                local_dt = fields.Datetime.context_timestamp(record, record.check_out)
                record.check_out_display = local_dt.strftime('%d/%m/%Y %H:%M:%S')
            else:
                record.check_out_display = ''

    @api.depends('check_in', 'check_out')
    def _compute_check_dates(self):
        for record in self:
            if record.check_in:
                local_check_in = fields.Datetime.context_timestamp(record, record.check_in)
                record.check_in_date = local_check_in.date()
            else:
                record.check_in_date = False
            if record.check_out:
                local_check_out = fields.Datetime.context_timestamp(record, record.check_out)
                record.check_out_date = local_check_out.date()
            else:
                record.check_out_date = False

    def write(self, vals):
        """
        Sobreescribe el método write para validar y asignar tags/estatus automáticamente
        cuando se actualizan campos relevantes de check-in.
        """
        result = super().write(vals)
        checkin_fields = {'check_in_latitude', 'check_in_longitude', 'check_in_geofence_ids', 'check_in', 'employee_id'}
        # Solo ejecutar la validación si se actualiza algún campo relevante de check-in
        if checkin_fields.intersection(vals.keys()):
            for attendance in self:
                attendance._validate_tags_and_status()
        return result

    def _validate_tags_and_status(self):
        """
        Valida y asigna los tags y el estatus de la asistencia según la lógica de geocerca y retardo.
        """
        tag_retardo = self.env.ref('hr_attendance_estevez.attendance_tag_retardo', raise_if_not_found=False)
        tag_sin_geocerca = self.env.ref('hr_attendance_estevez.attendance_tag_sin_geocerca', raise_if_not_found=False)
        tag_fuera_geocerca = self.env.ref('hr_attendance_estevez.attendance_tag_fuera_geocerca', raise_if_not_found=False)
        tag_aprobado_auto = self.env.ref('hr_attendance_estevez.attendance_tag_aprobado_auto', raise_if_not_found=False)

        tag_ids = []
        estado = 'pending'
        check_in = self.check_in
        employee = self.employee_id
        # Validación de retardo
        if check_in:
            local_dt = fields.Datetime.context_timestamp(self, check_in)
            if (local_dt.hour > 8 or (local_dt.hour == 8 and local_dt.minute > 10)):
                if tag_retardo:
                    tag_ids.append(tag_retardo.id)
        # Validación de geocerca
        geocercas = self.env['hr.attendance.geofence'].search([('employee_ids', 'in', [employee.id])])
        geocerca_ids = [g.id for g in geocercas]
        check_in_geofence_ids = self.check_in_geofence_ids.ids if self.check_in_geofence_ids else []
        if not geocercas:
            if tag_sin_geocerca:
                tag_ids.append(tag_sin_geocerca.id)
        else:
            dentro_geocerca = False
            if check_in_geofence_ids:
                dentro_geocerca = any(geofence_id in geocerca_ids for geofence_id in check_in_geofence_ids)
            if not dentro_geocerca:
                if tag_fuera_geocerca:
                    tag_ids.append(tag_fuera_geocerca.id)
        # Si no hay tags de retardo, sin geocerca o fuera de geocerca, se aprueba automáticamente
        if not tag_ids:
            estado = 'approved'
            if tag_aprobado_auto:
                tag_ids.append(tag_aprobado_auto.id)
        self.status = estado
        self.tag_ids = [(6, 0, tag_ids)]

    @api.model
    def auto_close_open_attendances(self):
        """
        🕚 CRONJOB: Cierra automáticamente todas las asistencias abiertas a las 11:58 PM
        Busca asistencias con check_in pero sin check_out y las cierra automáticamente
        """
        try:
            open_attendances = self.search([
                ('check_out', '=', False),
                ('check_in', '!=', False)
            ])
            if not open_attendances:
                _logger.info("🟢 No hay asistencias abiertas para cerrar")
                return True
            for attendance in open_attendances:
                try:
                    # Cierre automático: check_out igual a check_in
                    attendance.write({
                        'is_auto_closed': True,
                        'check_out': attendance.check_in,
                    })
                except Exception as e:
                    _logger.error(f"❌ Error cerrando asistencia ID {attendance.id}: {str(e)}")
                    continue
            return True
        except Exception as e:
            _logger.error(f"❌ Error en cronjob auto_close_open_attendances: {str(e)}")
            return False
    # Hereda y expone un método para ser llamado desde el modelo employee custom
    @api.model
    def close_attendance_as_auto(self, attendance):
        """
        Cierra una asistencia abierta asignando check_out igual a check_in y marcando is_auto_closed.
        """
        attendance.write({
            'is_auto_closed': True,
            'check_out': attendance.check_in,
        })