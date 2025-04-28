from odoo import models, fields
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)

class HrMemorandum(models.Model):
    _name = 'hr.memorandum'
    _description = 'Actas Administrativas'
    _order = 'create_date desc'

    employee_id = fields.Many2one('hr.employee', string='Empleado', required=True, ondelete='cascade')
    date = fields.Datetime(string='Fecha del Acta', required=True)
    description = fields.Html(string='Descripción / Hechos', required=True, sanitize=True)
    fraction = fields.Char(string='Fracción')
    article = fields.Char(string='Artículo')
    administrative_type = fields.Char(string='Tipo Acta administrativa') 

    def download_memorandum_report(self):
        """Generates a PDF report for the memorandum."""
        self.ensure_one()  # Ensure only one record is processed
        _logger.info("Downloading memorandum report for record: %s", self)

        return {
            'type': 'ir.actions.report',
            'report_name': 'hr_estevez.report_hr_employee_memorandum',
            'report_type': 'qweb-pdf',
            'model': self._name,
            'res_id': self.id,
        }

    def action_save_memorandum(self):
        """Saves the memorandum and closes the modal."""
        self.ensure_one()  # Ensure only one record is processed
        # Perform any additional save logic here if needed
        return {
            'type': 'ir.actions.act_window_close',
        }
    
    def get_formatted_date(self):
        """Devuelve la fecha formateada como: 'las 11:00 hrs del día 15 de abril del 2025'."""
        self.ensure_one()  # Asegúrate de que solo se procese un registro
        if not self.date:
            return ""

        # Mapeo manual de los meses en inglés a español
        months_mapping = {
            "January": "enero",
            "February": "febrero",
            "March": "marzo",
            "April": "abril",
            "May": "mayo",
            "June": "junio",
            "July": "julio",
            "August": "agosto",
            "September": "septiembre",
            "October": "octubre",
            "November": "noviembre",
            "December": "diciembre",
        }

        # Convertir la fecha a un objeto datetime
        date_obj = datetime.strptime(str(self.date), '%Y-%m-%d %H:%M:%S')

        # Ajustar la hora (por ejemplo, restar 4 horas para México)
        adjusted_date = date_obj + timedelta(hours=-4)

        # Obtener el nombre del mes en inglés y mapearlo al español
        month_name_english = adjusted_date.strftime("%B")
        month_name_spanish = months_mapping.get(month_name_english, month_name_english)

        # Extraer la hora en formato de 24 horas
        time_str = adjusted_date.strftime("%H:%M")

        # Formatear la fecha manualmente
        formatted_date = f"las {time_str} hrs del día {adjusted_date.day} de {month_name_spanish} del {adjusted_date.year}"
        return formatted_date
        