from odoo import models, fields, api
from datetime import datetime, timedelta
from odoo.exceptions import UserError
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
    fraction = fields.Char(string='Fraccion')
        # Campo SELECT con versiones cortas
    fraction_code = fields.Selection(
        [
            ('i', 'I. Engañar con certificados falsos'),
            ('ii', 'II. Faltas de probidad u honradez'),
            ('iii', 'III. Actos contra compañeros'),
            ('iv', 'IV. Actos graves fuera del servicio'),
            ('v', 'V. Perjuicios materiales intencionales'),
            ('vi', 'VI. Perjuicios graves por negligencia'),
            ('vii', 'VII. Comprometer seguridad del establecimiento'),
            ('viii', 'VIII. Actos inmorales o acoso sexual'),
            ('ix', 'IX. Revelar secretos de fabricación'),
            ('x', 'X. Más de 3 faltas en 30 días'),
            ('xi', 'XI. Desobedecer al patrón'),
            ('xii', 'XII. Negarse a medidas de seguridad'),
            ('xiii', 'XIII. Asistir en estado de embriaguez'),
            ('xiv', 'XIV. Sentencia de prisión'),
            ('xivbis', 'XIV Bis. Falta de documentos'),
            ('xv', 'XV. Causas análogas'),
        ],
        string="Fracción"
    )
    # Campo que GUARDA el texto completo
    fraction_full_text = fields.Text(
        string="Texto Completo de la Fracción"
    )
    
    # Diccionario con todos los textos completos
    FRACTION_TEXTS = {
        'i': 'I. Engañarlo el trabajador o en su caso, el sindicato que lo hubiese propuesto o recomendado con certificados falsos o referencias en los que se atribuyan al trabajador capacidad, aptitudes o facultades de que carezca. Esta causa de rescisión dejará de tener efecto después de treinta días de prestar sus servicios el trabajador; LEY FEDERAL DEL TRABAJO CÁMARA DE DIPUTADOS DEL H. CONGRESO DE LA UNIÓN Secretaría General Secretaría de Servicios Parlamentarios Última Reforma DOF 21-02-2025 15 de 450',
        'ii': 'II. Incurrir el trabajador, durante sus labores, en faltas de probidad u honradez, en actos de violencia, amagos, injurias o malos tratamientos en contra del patrón, sus familiares o del personal directivo o administrativo de la empresa o establecimiento, o en contra de clientes y proveedores del patrón, salvo que medie provocación o que obre en defensa propia; Fracción reformada DOF 30-11-2012',
        'iii': 'III. Cometer el trabajador contra alguno de sus compañeros, cualquiera de los actos enumerados en la fracción anterior, si como consecuencia de ellos se altera la disciplina del lugar en que sedesempeña el trabajo',
        'iv': 'IV. Cometer el trabajador, fuera del servicio, contra el patrón, sus familiares o personal directivo administrativo, alguno de los actos a que se refiere la fracción II, si son de tal manera graves que hagan imposible el cumplimiento de la relación de trabajo;',
        'v': 'V. Ocasionar el trabajador, intencionalmente, perjuicios materiales durante el desempeño de las labores o con motivo de ellas, en los edificios, obras, maquinaria, instrumentos, materias primas y demás objetos relacionados con el trabajo;',
        'vi': 'VI. Ocasionar el trabajador los perjuicios de que habla la fracción anterior siempre que sean graves, sin dolo, pero con negligencia tal, que ella sea la causa única del perjuicio;',
        'vii': 'VII. Comprometer el trabajador, por su imprudencia o descuido inexcusable, la seguridad del establecimiento o de las personas que se encuentren en él;',
        'viii': 'VIII. Cometer el trabajador actos inmorales o de hostigamiento y/o acoso sexual contra cualquier persona en el establecimiento o lugar de trabajo; Fracción reformada DOF 30-11-2012',
        'ix': 'IX. Revelar el trabajador los secretos de fabricación o dar a conocer asuntos de carácter reservado, con perjuicio de la empresa;',
        'x': 'X. Tener el trabajador más de tres faltas de asistencia en un período de treinta días, sin permiso del patrón o sin causa justificada;',
        'xi': 'XI. Desobedecer el trabajador al patrón o a sus representantes, sin causa justificada, siempre que se trate del trabajo contratado;',
        'xii': 'XII. Negarse el trabajador a adoptar las medidas preventivas o a seguir los procedimientos indicados para evitar accidentes o enfermedades;',
        'xiii': 'XIII. Concurrir el trabajador a sus labores en estado de embriaguez o bajo la influencia de algún narcótico o droga enervante, salvo que, en este último caso, exista prescripción médica. Antes de iniciar su servicio, el trabajador deberá poner el hecho en conocimiento del patrón y presentar la prescripción suscrita por el médico;',
        'xiv': 'XIV. La sentencia ejecutoriada que imponga al trabajador una pena de prisión, que le impida el cumplimiento de la relación de trabajo; Fracción reformada DOF 30-11-2012',
        'xivbis': 'XIV Bis. La falta de documentos que exijan las leyes y reglamentos, necesarios para la prestación del servicio cuando sea imputable al trabajador y que exceda del periodo a que se refiere la fracción IV del artículo 43; y Fracción adicionada DOF 30-11-2012 LEY FEDERAL DEL TRABAJO CÁMARA DE DIPUTADOS DEL H. CONGRESO DE LA UNIÓN Secretaría General Secretaría de Servicios Parlamentarios Última Reforma DOF 21-02-2025 16 de 450' ,
        'xv': 'XV. Las análogas a las establecidas en las fracciones anteriores, de igual manera graves y de consecuencias semejantes en lo que al trabajo se refiere.'                
    }
    
    @api.onchange('fraction_code')
    def _onchange_fraction_code(self):
        """Cuando se cambia la selección, actualiza automáticamente el texto completo"""
        if self.fraction_code and self.fraction_code in self.FRACTION_TEXTS:
            self.fraction_full_text = self.FRACTION_TEXTS[self.fraction_code]
        else:
            self.fraction_full_text = ''
    article = fields.Char(string='Artículo', default="47.- Son causas de rescisión de la relación de trabajo, sin responsabilidad para el patrón:")
    administrative_type = fields.Selection(
        [
            ('velocidad', 'Velocidad'),
            ('faltas', 'Faltas'),
            ('estado_ebriedad', 'Estado de ebriedad'),
            ('consumo', 'Consumo de sustancias'),
            ('probidad', 'Falta de probidad'),
            ('desempeño', 'Bajo desempeño'),
        ],
        string= "Tipo de Acta Administrativa"
    )

    def download_memorandum_report(self):
        self.ensure_one()

        report_map = {
            'velocidad': 'hr_estevez.action_report_memorandum_velocidad',
            'faltas': 'hr_estevez.action_report_memorandum_faltas',
            'estado_ebriedad': 'hr_estevez.action_report_memorandum_ebriedad',
            'desempeño': 'hr_estevez.action_report_memorandum_desempeño',
            # si agregas más tipos, solo los añades aquí
        }

        report_action = report_map.get(self.administrative_type)

        if not report_action:
            raise UserError("No existe un formato definido para este tipo de acta.")

        return self.env.ref(report_action).report_action(self)


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
