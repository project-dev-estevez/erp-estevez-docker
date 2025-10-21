# wizards/payroll_report_wizard.py
from odoo import models, fields, _


from datetime import date, timedelta

class PayrollReportWizard(models.TransientModel):
    _name = 'payroll.report.wizard'
    _description = 'Wizard para generar reporte de nómina'

    def _default_date_start(self):
        today = date.today()
        return today.replace(day=1)

    def _default_date_end(self):
        today = date.today()
        next_month = today.replace(day=28) + timedelta(days=4)
        return next_month - timedelta(days=next_month.day)

    date_start = fields.Date(string='Fecha inicial', required=True, default=_default_date_start)
    date_end = fields.Date(string='Fecha final', required=True, default=_default_date_end)
    company_id = fields.Many2one('res.company', string='Empresa', required=False)
    department_id = fields.Many2one('hr.department', string='Departamento (opcional)', required=False)

    def action_generate_report(self):
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
