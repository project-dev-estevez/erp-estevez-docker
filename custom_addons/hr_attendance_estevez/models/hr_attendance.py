from odoo import models, fields, api
from datetime import datetime

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
        default=lambda self: self._get_default_status(),
        tracking=True, 
        required=True
    )

    @api.model
    def _get_default_status(self):
        check_in = self._context.get('default_check_in')
        if check_in:
            try:
                check_in_dt = datetime.strptime(check_in, '%Y-%m-%d %H:%M:%S')
                if check_in_dt.hour > 8 or (check_in_dt.hour == 8 and check_in_dt.minute > 15):
                    return 'retarded'
            except Exception:
                pass
        return 'pending'