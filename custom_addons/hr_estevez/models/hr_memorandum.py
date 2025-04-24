from odoo import models, fields

class HrMemorandum(models.Model):
    _name = 'hr.memorandum'
    _description = 'Actas Administrativas'
    _order = 'create_date desc'

    employee_id = fields.Many2one('hr.employee', string='Empleado', required=True, ondelete='cascade')
    date = fields.Date(string='Fecha del Acta', required=True)
    description = fields.Html(string='Descripción / Hechos', required=True, sanitize=True)
    fraction = fields.Char(string='Fracción')
    article = fields.Char(string='Artículo')
    administrative_type = fields.Char(string='Tipo Acta administrativa') 

    def download_memorandum_report(self):
        """Generates a PDF report for the memorandum."""
        self.ensure_one()  # Ensure only one record is processed
        return {
            'type': 'ir.actions.report',
            'report_name': 'hr_estevez.report_hr_employee_memorandum',
            'report_type': 'qweb-pdf',
            'model': self._name,
            'res_id': self.id,
        }

    def action_save_memorandum(self):
        """Saves the memorandum without triggering the report generation."""
        self.ensure_one()  # Ensure only one record is processed
        # Perform any additional save logic here if needed
        return True
    