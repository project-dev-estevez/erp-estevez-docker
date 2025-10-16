from odoo import models, fields, api
from datetime import datetime, timezone, timedelta as td
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
        ('retarded', 'Retardado'),
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
                
            closed_count = 0
            
            for attendance in open_attendances:
                try:
                    # 🌎 TIMEZONE: Obtener el timezone del usuario/empresa
                    user_tz = self.env.user.tz or 'America/Mexico_City'
                    
                    # 🕐 Convertir check_in a timezone local para trabajar con fechas correctas
                    check_in_utc = attendance.check_in
                    
                    # 🌎 Convertir a timezone local (México) para calcular el día correcto
                    check_in_local = fields.Datetime.context_timestamp(self, check_in_utc)
                    check_in_date_local = check_in_local.date()
                    
                    # 🎯 Crear check_out a las 23:58:00 en timezone local
                    check_out_local = check_in_local.replace(
                        hour=23, 
                        minute=58, 
                        second=0, 
                        microsecond=0
                    )
                    
                    # 🔄 Convertir de vuelta a UTC para almacenar en base de datos
                    # Crear datetime naive en timezone local y luego convertir a UTC
                    mexico_offset = td(hours=-5)  # México está UTC-6 (o UTC-5 en horario de verano)
                    check_out_utc = check_out_local.replace(tzinfo=timezone(mexico_offset)).astimezone(timezone.utc).replace(tzinfo=None)
                    
                    # 📅 CORRECCIÓN: Restar 1 día para que el check_out sea del mismo día que check_in
                    check_out_utc = check_out_utc - td(days=1)
                    
                    # 📅 Log detallado para debugging
                    _logger.info(f"📊 Procesando asistencia ID {attendance.id}:")
                    _logger.info(f"   Empleado: {attendance.employee_id.name}")
                    _logger.info(f"   User timezone: {user_tz}")
                    _logger.info(f"   Check-in UTC: {check_in_utc}")
                    _logger.info(f"   Check-in Local: {check_in_local}")
                    _logger.info(f"   Fecha local: {check_in_date_local}")
                    _logger.info(f"   Check-out Local: {check_out_local}")
                    _logger.info(f"   Check-out UTC: {check_out_utc}")
                    
                    # ✅ Actualizar la asistencia
                    attendance.write({
                        'check_out': check_out_utc,
                    })
                    
                    closed_count += 1
                    _logger.info(
                        f"✅ Asistencia cerrada automáticamente - Empleado: {attendance.employee_id.name} "
                        f"Check-in: {attendance.check_in} -> Check-out: {check_out_utc}"
                    )
                    
                except Exception as e:
                    _logger.error(f"❌ Error cerrando asistencia ID {attendance.id}: {str(e)}")
                    continue
            
            _logger.info(f"🎯 Cronjob completado: {closed_count} asistencias cerradas automáticamente")
            return True
            
        except Exception as e:
            _logger.error(f"❌ Error en cronjob auto_close_open_attendances: {str(e)}")
            return False