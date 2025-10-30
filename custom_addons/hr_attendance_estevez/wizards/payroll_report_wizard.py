# wizards/payroll_report_wizard.py
from odoo import models, fields, _
from odoo.exceptions import UserError

class PayrollReportWizard(models.TransientModel):
    _name = 'payroll.report.wizard'
    _description = 'Wizard para generar reporte de nómina'

    date_start = fields.Date(
        string='Fecha inicio', 
        required=True, 
        default=lambda self: fields.Date.context_today(self).replace(day=1)
    )

    date_end = fields.Date(
        string='Fecha final', 
        required=True, 
        default=lambda self: fields.Date.context_today(self)
    )

    company_id = fields.Many2one(
        'res.company', 
        string='Empresa', 
        required=False
    )

    department_id = fields.Many2one(
        'hr.department', 
        string='Departamento', 
        required=False
    )

    def _validate_dates(self):
        today = fields.Date.context_today(self)
        for wizard in self:
            if wizard.date_end > today:
                raise UserError("La fecha final no puede ser mayor que la fecha actual.")
            if wizard.date_end < wizard.date_start:
                raise UserError("La fecha final no puede ser menor que la fecha inicial.")

    def action_generate_report(self):
        self._validate_dates()
        data = {
            'date_start': self.date_start.isoformat() if self.date_start else False,
            'date_end': self.date_end.isoformat() if self.date_end else False,
            'company_id': self.company_id.id if self.company_id else False,
            'department_id': self.department_id.id if self.department_id else False,
        }
        report_action = self.env.ref('hr_attendance_estevez.report_payroll_xlsx').report_action(self, data=data)
        report_action['close_on_report_download'] = True
        report_action['type'] = 'ir.actions.report'
        return report_action
