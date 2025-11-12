from odoo import models, fields, api
from datetime import datetime, timedelta
import logging
import json
import requests

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
    
    def _sync_codeigniter(self, operation='create'):
        """Sincroniza el memorandum con CodeIgniter"""
        api_url = self.env['ir.config_parameter'].get_param('codeigniter.api_url')
        api_token = self.env['ir.config_parameter'].get_param('codeigniter.api_token')
        
        if not api_url or not api_token:
            _logger.error("Configuración de API para CodeIgniter faltante")
            return False

        # Preparar payload
        employee = self.employee_id
        payload = {
            'odoo_id': self.id,
            'employee_odoo_id': employee.id,
            'date': self.date.isoformat() if self.date else None,
            'description': self.description or '',
            'fraction': self.fraction or '',
            'article': self.article or '',
            'administrative_type': self.administrative_type or '',
            'operation': operation,
        }

        try:
            # Determinar endpoint y método HTTP
            endpoint = f"{api_url}/memorandums"
            if operation == 'update' and self.ci_id:
                endpoint = f"{endpoint}/{self.ci_id}"
                http_method = requests.put
            else:
                http_method = requests.post
            
            # Enviar solicitud
            headers = {
                'Authorization': f'Bearer {api_token}',
                'Content-Type': 'application/json'
            }
            
            response = http_method(
                endpoint,
                json=payload,
                headers=headers,
                timeout=30,
                verify=False
            )
            
            _logger.info(f"Respuesta CI para memorandum: {response.status_code} - {response.text}")
            
            if response.status_code in (200, 201):
                response_data = response.json()
                self.write({
                    'synced_to_ci': True,
                    'ci_id': response_data.get('id', False)
                })
                return True
            else:
                _logger.error(f"Error CI: {response.status_code} - {response.text}")
                return False
                        
        except Exception as e:
            _logger.error(f"Error de conexión con CodeIgniter: {str(e)}")
            return False

    @api.model_create_multi
    def create(self, vals_list):
        records = super(HrMemorandum, self).create(vals_list)
        # Sincronizar después de crear
        for record in records:
            record._sync_codeigniter('create')
        return records

    def write(self, vals):
        res = super(HrMemorandum, self).write(vals)
        # Sincronizar después de actualizar
        for record in self:
            record._sync_codeigniter('update')
        return res
