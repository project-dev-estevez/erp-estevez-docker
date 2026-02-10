from odoo import models, fields
import logging

_logger = logging.getLogger(__name__)

class HrEmployeeReactivateWizard(models.TransientModel):
    _name = 'hr.employee.reactivate.wizard'
    _description = 'Wizard para Reactivar Empleado'

    employee_id = fields.Many2one('hr.employee', string='Empleado', required=True)
    reactivation_date = fields.Datetime(string='Fecha de Alta', required=True, default=fields.Datetime.now)
    reason = fields.Text(string='Motivo', required=True)

    def confirm_reactivate(self):
        """Confirma la reactivación del empleado."""
        self.ensure_one()
        # Reactivar empleado
        self.employee_id.write({
            'active': True,
        })
        
        # Registrar en el historial
        self.env['hr.employee.history'].create({
            'employee_id': self.employee_id.id,
            'date': self.reactivation_date,
            'status': 'alta',
            'reason': self.reason,
        })
        
        # Sincronizar con CodeIgniter
        try:
            self.employee_id._sync_codeigniter_unarchive()
        except Exception as e:
            _logger.error(f"Error en sincronización de reactivación: {str(e)}")
            # No detener el proceso, solo registrar error
            
        return True