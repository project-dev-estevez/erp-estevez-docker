from odoo import models, fields

class AttendanceReportWizard(models.TransientModel):
    _name = 'attendance.report.wizard'
    _description = 'Wizard para generar reporte de asistencias'

    company_id = fields.Many2one('res.company', string='Empresa', required=True)
    payment_type = fields.Selection([
        ('hourly', 'Por hora'),
        ('monthly', 'Mensual'),
        ('contract', 'Por contrato'),
    ], string='Tipo de pago', required=True)

    def action_generate_report(self):
        data = {
            'company_id': self.company_id.id,
            'payment_type': self.payment_type,
        }
        return self.env.ref('hr_attendance_estevez.report_attendance_xlsx').report_action(self, data=data)
