# wizards/payroll_report_wizard.py
from odoo import models, fields

class PayrollReportWizard(models.TransientModel):
    _name = 'payroll.report.wizard'
    _description = 'Wizard para generar reporte de nómina'

    date_start = fields.Date(string='Fecha inicial', required=True)
    date_end = fields.Date(string='Fecha final', required=True)
    department_id = fields.Many2one('hr.department', string='Departamento (opcional)')

    def action_generate_report(self):
        data = {
            'date_start': self.date_start.isoformat() if self.date_start else False,
            'date_end': self.date_end.isoformat() if self.date_end else False,
            'department_id': self.department_id.id if self.department_id else False,
        }
        return self.env.ref('hr_attendance_estevez.report_payroll_xlsx').report_action(self, data=data)
