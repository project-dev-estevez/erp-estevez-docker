from odoo import models, fields, api

class HrEmployeeReactivateWizard(models.TransientModel):
    _name = 'hr.employee.reactivate.wizard'
    _description = 'Wizard para Reactivar Empleado'

    employee_id = fields.Many2one('hr.employee', string='Empleado', required=True)
    reactivation_date = fields.Datetime(string='Fecha de Alta', required=True, default=fields.Date.today)
    reason = fields.Text(string='Motivo', required=True)

    def confirm_reactivate(self):
        """Confirma la reactivación del empleado."""
        self.ensure_one()
        self.employee_id.write({
            'active': True,
        })
        # Registrar la información adicional en un modelo relacionado si es necesario
        self.env['hr.employee.history'].create({
            'employee_id': self.employee_id.id,
            'date': self.reactivation_date,
            'status': 'alta',
            'reason': self.reason,
        })
        return True