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

    is_auto_closed = fields.Boolean(
        string='Cerrado Automáticamente',
        help='Indica si la asistencia fue cerrada automáticamente por el sistema',
        default=False,
        tracking=True
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