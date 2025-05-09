from odoo import models, fields, api

class HrEmployeeArchiveWizard(models.TransientModel):
    _name = 'hr.employee.archive.wizard'
    _description = 'Wizard para Archivar Empleado'

    employee_id = fields.Many2one('hr.employee', string='Empleado', required=True)
    termination_date = fields.Date(string='Fecha de Baja', required=True, default=fields.Date.today)
    possible_rehire = fields.Selection([
        ('viable', 'Viable'),
        ('inviable', 'Inviable'),
    ], string='Posible Recontratación')
    termination_type = fields.Selection([
        ('voluntary_resignation', 'Renuncia Voluntaria'),
        ('contract_end', 'Término de Contrato'),
        ('abandonment', 'Abandono'),
        ('dismissal_misconduct', 'Despido por Faltas Injustificadas'),
        ('dismissal_performance', 'Despido por Bajo Desempeño'),
        ('dismissal_probity', 'Despido por Falta de Probidad'),
    ], string='Tipo de Baja', required=True)
    reason = fields.Text(string='Motivo')

    def confirm_archive(self):
        """Confirma la baja del empleado."""
        self.ensure_one()
        self.employee_id.write({
            'active': False,
        })
        # Aquí puedes registrar la información adicional en un modelo relacionado si es necesario.
        return True