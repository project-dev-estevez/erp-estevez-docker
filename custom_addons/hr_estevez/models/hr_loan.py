from odoo import models, fields
import logging

_logger = logging.getLogger(__name__)

class HrLoan(models.Model):
    _name = 'hr.loan'
    _description = 'Préstamos y Anticipos'
    _order = 'create_date desc'

    employee_id = fields.Many2one('hr.employee', string='Empleado', required=True, ondelete='cascade')
    request_date = fields.Date(string='Fecha de Solicitud del Préstamo', required=True)
    application_date = fields.Date(string='Fecha de Aplicación del Préstamo', required=True)
    start_payment_date = fields.Date(string='Fecha de Inicio de Cobro', required=True)
    requested_amount = fields.Float(string='Monto Solicitado', required=True, help="Ingrese el monto solicitado. Ejemplo: 1000")
    term = fields.Char(string='Plazo', help="Plazo del préstamo")
    disbursement_type = fields.Selection([
        ('loan', 'Préstamo'),
        ('advance', 'Anticipo')
    ], string='Tipo de Desembolso', required=True)
    discount_type = fields.Selection([
        ('weekly', 'Semanal'),
        ('biweekly', 'Quincenal')
    ], string='Tipo de Descuento', required=True)

    def format_requested_amount(self):
        """Devuelve el monto solicitado con el signo de pesos."""
        self.ensure_one()  # Asegúrate de que solo se procese un regi   stro
        return f"${self.requested_amount:,.2f}"

    def action_save_loan(self):
        """Guarda el préstamo y cierra el modal."""
        self.ensure_one()  # Asegúrate de que solo se procese un registro
        _logger.info("Saving loan record: %s", self)

    def download_loan_report(self):
        """Generates a PDF report for the memorandum."""
        self.ensure_one()  # Ensure only one record is processed
        _logger.info("Downloading memorandum report for record: %s", self)

        return {
            'type': 'ir.actions.report',
            'report_name': 'hr_estevez.report_hr_employee_loan',
            'report_type': 'qweb-pdf',
            'model': self._name,
            'res_id': self.id,
        }