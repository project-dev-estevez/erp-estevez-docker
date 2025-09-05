from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)

class HrEmployeeArchiveWizard(models.TransientModel):
    _name = 'hr.employee.archive.wizard'
    _description = 'Wizard para Archivar Empleado'

    employee_id = fields.Many2one('hr.employee', string='Empleado', required=True)
    termination_date = fields.Datetime(string='Fecha de Baja', required=True, default=fields.Datetime.now)
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
        # Archivar empleado
        self.employee_id.write({
            'active': False,
        })
        
        # Registrar la baja en el historial
        self.env['hr.employee.history'].create({
            'employee_id': self.employee_id.id,
            'date': self.termination_date,
            'status': 'baja',
            'reason': self.reason,
            'possible_rehire': self.possible_rehire,
            'termination_type': self.termination_type,
        })
        
        # Sincronizar con CodeIgniter
        try:
            self.employee_id._sync_codeigniter_archive()
        except Exception as e:
            _logger.error(f"Error en sincronización de baja: {str(e)}")
            # No detener el proceso, solo registrar error
            
        return True