import json
import logging
from odoo import api, models, fields, _
from odoo.exceptions import UserError
from datetime import date, timedelta, datetime
from dateutil.relativedelta import relativedelta
import re
import requests

_logger = logging.getLogger(__name__)

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    gender = fields.Selection([
        ('male', 'Masculino'),
        ('female', 'Femenino'),
        ('indistinct', 'Indistinto')  # Cambiar la etiqueta de 'other'
    ], groups="hr.group_hr_user", tracking=True)

    # Primera Columna en la Vista de Empleados
    names = fields.Char(string='Nombres')
    last_name = fields.Char(string='Apellido Paterno', required=False)
    mother_last_name = fields.Char(string='Apellido Materno')
    employee_number = fields.Char(string='Número de Empleado')
    project = fields.Char(string='Proyecto')

    # Segunda Columna en la Vista de Empleados 
    company_id = fields.Many2one('res.company', string='Company', compute='_compute_company', store=True, readonly=True)
    direction_id = fields.Many2one('hr.direction', string='Dirección')
    area_id = fields.Many2one('hr.area', string='Área')

    # Información de Trabajo
    imss_registration_date = fields.Date(string='Fecha de Alta en IMSS')
    payment_type = fields.Selection([
        ('weekly', 'Semanal'),
        ('biweekly', 'Quincenal'),
    ], string='Tipo de Pago')
    payroll_type = fields.Selection([
        ('cash', 'Efectivo'),
        ('mixed', 'Mixto'),
        ('imss', 'IMSS'),
    ], string='Tipo de Nómina')


    rfc = fields.Char(string='RFC')
    curp = fields.Char(string='CURP')
    nss = fields.Char(string='NSS')
    voter_key = fields.Char(string='Clave Elector')
    license_number = fields.Char(string='Número de Licencia')
    infonavit = fields.Boolean(string='Infonavit', default=False)
    private_colonia = fields.Char(string="Colonia")
    fiscal_zip = fields.Char(string="Fiscal ZIP")

    work_phone = fields.Char(string='Work Phone', compute=False)
    # coach_id = fields.Many2one('hr.employee', string='Instructor', compute=False, store=False)

    name = fields.Char(string='Nombre Completo', compute='_compute_full_name', store=True, readonly=True)
    age = fields.Integer(string='Edad', compute='_compute_age')

    country_id = fields.Many2one('res.country', string='País', default=lambda self: self.env.ref('base.mx').id)
    country_of_birth = fields.Many2one('res.country', string="Country of Birth", groups="hr.group_hr_user", tracking=True, default=lambda self: self.env.ref('base.mx').id)
    private_country_id = fields.Many2one("res.country", string="Private Country", groups="hr.group_hr_user", default=lambda self: self.env.ref('base.mx').id)
    is_mexico = fields.Boolean(string="Is Mexico", compute="_compute_is_mexico", store=False)

    marital = fields.Selection([
        ('single', 'Soltero(a)'),
        ('married', 'Casado(a)'),
        ('cohabitant', 'En Concubinato'),
        ('widower', 'Viudo(a)'),
        ('divorced', 'Divorciado(a)')
    ], string='Estado Civil', required=True, tracking=True)

    spouse_birthdate = fields.Date(string="Spouse Birthdate", groups="hr.group_hr_user", store=False)

    memorandum_ids = fields.One2many('hr.memorandum', 'employee_id', string='Actas Administrativas')
    loan_ids = fields.One2many('hr.loan', 'employee_id', string='Préstamos y Anticipos')

    vacation_period_ids = fields.One2many(
        'hr.vacation.period', 'employee_id', string="Periodos de Vacaciones"
    )

    emergency_contact_relationship = fields.Char(string="Parentesco del Primer Contacto")
    
    # Campos para el segundo contacto de emergencia
    emergency_contact_2 = fields.Char(string="Segundo Contacto")
    emergency_contact_relationship_2 = fields.Char(string="Parentesco del Segundo Contacto")
    emergency_phone_2 = fields.Char(string="Teléfono del Segundo Contacto")

    #Campos para asignaciones
    asset_assignment_ids = fields.One2many(
        'stock.assignment',
        'recipient_id',
        string='Activos Fijos',
        domain=[('category_type', '=', 'asset')]
    )
    
    tool_assignment_ids = fields.One2many(
        'stock.assignment',
        'recipient_id',
        string='Herramientas',
        domain=[('category_type', '=', 'tool')]
    )
    
    consumable_assignment_ids = fields.One2many(
        'stock.assignment',
        'recipient_id',
        string='Consumibles',
        domain=[('category_type', '=', 'consumable')]
    )

    employment_start_date = fields.Date(string='Fecha de Ingreso', tracking=True)

    years_of_service = fields.Float(compute='_compute_years_of_service', string='Años de servicio', store=True)
    entitled_days = fields.Float(compute='_compute_entitled_days', string='Con derecho a', store=True)
    vacation_days_taken = fields.Float(compute='_compute_days_taken', string='Días de vacaciones disfrutados', store=True)
    vacation_days_available = fields.Float(compute='_compute_days_available', string='Días vacaciones disponibles', store=True)
    vacation_period_ids = fields.One2many('hr.vacation.period', 'employee_id')

    leave_ids = fields.One2many('hr.leave', 'period_id')

    def _create_vacation_period(self, employee, start_date, end_date):
        # Calcular el inicio y fin del periodo basado en años calendario
        year_start = start_date
        while year_start < end_date:
            year_end = year_start.replace(year=year_start.year + 1) - timedelta(days=1)
            if year_end > end_date:
                year_end = end_date

            entitled_days = 12 + ((year_start.year - start_date.year) * 2) if (year_start.year - start_date.year) < 5 else 22
            days_taken = 0  # Inicialmente 0

            self.env['hr.vacation.period'].create({
                'employee_id': employee.id,
                'year_start': year_start,
                'year_end': year_end,
                'entitled_days': entitled_days,
                'days_taken': days_taken,
            })

            # Avanzar al siguiente año
            year_start = year_start.replace(year=year_start.year + 1)

    @api.depends('employment_start_date')
    def _compute_years_of_service(self):
        today = fields.Date.today()
        for record in self:
            if record.employment_start_date:
                delta = today - record.employment_start_date
                record.years_of_service = delta.days / 365.0
            else:
                record.years_of_service = 0

    @api.depends('years_of_service')
    def _compute_entitled_days(self):
        for record in self:
            years = int(record.years_of_service)
            if years < 1:
                record.entitled_days = 0
            elif years == 1:
                record.entitled_days = 12
            elif years == 2:
                record.entitled_days = 14
            elif years == 3:
                record.entitled_days = 16
            elif years == 4:
                record.entitled_days = 18
            elif years == 5:
                record.entitled_days = 20
            else:
                # Años adicionales: +2 días por cada 5 años después del 5to
                additional_years = years - 5
                additional_days = (additional_years // 5) * 2
                record.entitled_days = 20 + additional_days

    @api.depends('vacation_period_ids.days_taken')  # Mantener esta dependencia
    def _compute_days_taken(self):
        for record in self:
            # Suma directa sin dependencia cruzada
            record.vacation_days_taken = sum(
                period.days_taken for period in record.vacation_period_ids
            )

    @api.depends('entitled_days', 'vacation_days_taken')
    def _compute_days_available(self):
        for record in self:
            record.vacation_days_available = record.entitled_days - record.vacation_days_taken

    def action_open_memorandum_form(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Nueva Acta Administrativa',
            'res_model': 'hr.memorandum',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_employee_id': self.id},
        }
    
    def action_open_loan_form(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Nuevo Préstamo o Anticipo',
            'res_model': 'hr.loan',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_employee_id': self.id},
        }

    @api.depends('country_id')
    def _compute_is_mexico(self):
        for record in self:
            record.is_mexico = record.country_id.code == 'MX'

    @api.depends('names', 'last_name', 'mother_last_name')
    def _compute_full_name(self):
        for record in self:
            record.name = f"{record.names} {record.last_name} {record.mother_last_name}"

    @api.onchange('names', 'last_name', 'mother_last_name')
    def _onchange_full_name(self):
        for record in self:
            names = record.names or ''
            last_name = record.last_name or ''
            mother_last_name = record.mother_last_name or ''
            record.name = f"{names} {last_name} {mother_last_name}".strip()

    def _sync_codeigniter(self, employee, operation='create'):
        api_url = self.env['ir.config_parameter'].get_param('codeigniter.api_url')
        api_token = self.env['ir.config_parameter'].get_param('codeigniter.api_token')
        
        if not api_url or not api_token:
            _logger.error("Configuración de API para CodeIgniter faltante")
            return False
        

        # Asegurar valores no nulos
        payload = {
            'nombre': employee.names or '',
            'apellido_paterno': employee.last_name or '',
            'apellido_materno': employee.mother_last_name or '',
            'curp': employee.curp or '',
            'email': employee.work_email or '',
            'sexo': employee.gender or 'other',
            'numero_empleado': employee.employee_number or '',
            'nss': employee.nss or '',
            'fecha_nacimiento': employee.birthday.strftime('%Y-%m-%d') if employee.birthday else None,
            'imss_registration_date': employee.imss_registration_date.strftime('%Y-%m-%d') if employee.imss_registration_date else None,
            'nacionalidad': 'Mexico',
            'clave_elector': employee.voter_key or '',
            'odoo_id': employee.id,
            'payment_type': employee.payment_type or '',
            'work_phone': employee.work_phone or '',
            'working_hours': employee.resource_calendar_id.display_name or '',
            'private_street': employee.private_street or '',
            'private_street2': employee.private_street2 or '',
            'private_colonia': employee.private_colonia or '',
            'private_zip': employee.private_zip or '',
            'fiscal_zip': employee.fiscal_zip or '',
            'private_email': employee.private_email or '',
            'private_phone': employee.private_phone or '',
            'infonavit': bool(employee.infonavit),
            'license_number': employee.license_number or '',
            'study_field': employee.study_field or '',
            'study_school': employee.study_school or '',
            'marital': employee.marital or '',
            'children': employee.children or 0,
            'job_title': employee.job_title or ''
        }

        try:
            import json
             # 1. Crear la sesión primero
            session = requests.Session()
            session.verify = False
            
            # 2. Preparar headers comunes
            headers = {
                'Authorization': f'Bearer {api_token}',
                'Content-Type': 'application/json; charset=utf-8'
            }
            json_payload = json.dumps(payload, ensure_ascii=False)
        
            # Codificar a bytes UTF-8 explícitamente
            utf8_payload = json_payload.encode('utf-8')
            
            _logger.info(f"Longitud UTF-8: {len(utf8_payload)} bytes")
            _logger.info(f"Contenido: {json_payload[:100]}...")  # Muestra inicio
            
            # Enviar como bytes
            endpoint = api_url
            if operation == 'update':
                endpoint = f"{api_url}/empleados/{employee.id}"
                http_method = requests.put
            else:
                http_method = requests.post
            
            # Enviar con el método adecuado
            response = http_method(
                endpoint,
                data=utf8_payload,
                headers={
                    'Authorization': f'Bearer {api_token}',
                    'Content-Type': 'application/json; charset=utf-8',
                    'Content-Length': str(len(utf8_payload))
                },
                timeout=30,
                verify=False
            )
            
            
            _logger.info(f"Respuesta de CodeIgniter: {response.status_code} - {response.text}")
            
            if (operation == 'create' and response.status_code == 201) or \
            (operation == 'update' and response.status_code in (200, 204)):
                _logger.info(f"Sincronización exitosa para empleado {employee.id}")
                return True
            else:
                _logger.error(f"Error en CI: {response.status_code} - {response.text}")
                return False
                        
        except Exception as e:
            _logger.error(f"Error de conexión: {str(e)}")
            return False

    @api.model
    def create(self, vals):
        # Construir nombre completo
        if 'names' in vals or 'last_name' in vals or 'mother_last_name' in vals:
            names = vals.get('names', '').strip()
            last_name = vals.get('last_name', '').strip()
            mother_last_name = vals.get('mother_last_name', '').strip()
            vals['name'] = f"{names} {last_name} {mother_last_name}".strip()
        
        # Crear empleado
        employee = super(HrEmployee, self).create(vals)
        
        # Generar períodos de vacaciones si hay fecha de ingreso
        if vals.get('employment_start_date'):
            employee.generate_vacation_periods()
        
        # Sincronizar con CodeIgniter
        try:
            _logger.info("Intentando sincronizar con CodeIgniter")
            self._sync_codeigniter(employee, 'create')
        except Exception as e:
            _logger.error(f"Error en sincronización: {str(e)}")
        
        return employee

    def write(self, vals):
        # Construir nombre completo si cambian los componentes
        if 'name' not in vals and ('names' in vals or 'last_name' in vals or 'mother_last_name' in vals):
            names_val = vals.get('names', self.names) or ''
            last_name_val = vals.get('last_name', self.last_name) or ''
            mother_last_name_val = vals.get('mother_last_name', self.mother_last_name) or ''
            vals['name'] = f"{names_val} {last_name_val} {mother_last_name_val}".strip()
        
        # Regenerar períodos solo si cambia la fecha de ingreso Y no hay días tomados
        if 'employment_start_date' in vals:
            for employee in self:
                # Si se está estableciendo una fecha de ingreso vacía, eliminar períodos existentes
                if not vals['employment_start_date']:
                    employee.vacation_period_ids.unlink()
                    continue
                    
                # Verificar si hay días tomados antes de regenerar
                if any(period.days_taken > 0 for period in employee.vacation_period_ids):
                    raise UserError("No se puede cambiar la fecha de ingreso porque hay días de vacaciones ya tomados. Elimine manualmente los periodos existentes primero.")
                
                # Eliminar periodos existentes
                employee.vacation_period_ids.unlink()

        # Llamar al write original
        res = super().write(vals)
        
        # Generar nuevos períodos después de guardar
        if 'employment_start_date' in vals:
            for employee in self:
                if employee.employment_start_date:
                    employee.generate_vacation_periods()
        
        # Sincronizar con CodeIgniter después de guardar
        try:
            for employee in self:
                _logger.info(f"Iniciando sincronización de actualización para {employee.name}")
                employee._sync_codeigniter(employee, 'update')
        except Exception as e:
            _logger.error(f"Error en sincronización de actualización: {str(e)}")

        return res
    
    @api.depends('birthday')
    def _compute_age(self):
        for record in self:
            if record.birthday:
                today = date.today()
                record.age = today.year - record.birthday.year - ((today.month, today.day) < (record.birthday.month, record.birthday.day))
            else:
                record.age = 0

    def _format_phone_number(self, phone_number):
        if phone_number and not phone_number.startswith('+52'):
            phone_number = '+52 ' + re.sub(r'(\d{3})(\d{3})(\d{4})', r'\1 \2 \3', phone_number)
        return phone_number

    @api.onchange('work_phone')
    def _onchange_work_phone(self):
        if self.work_phone:
            self.work_phone = self._format_phone_number(self.work_phone)

    @api.onchange('private_phone')
    def _onchange_private_phone(self):
        if self.private_phone:
            self.private_phone = self._format_phone_number(self.private_phone)

    @api.onchange('emergency_phone')
    def _onchange_emergency_phone(self):
        if self.emergency_phone:
            self.emergency_phone = self._format_phone_number(self.emergency_phone)

    @api.onchange('emergency_phone_2')
    def _onchange_emergency_phone_2(self):
        if self.emergency_phone_2:
            self.emergency_phone_2 = self._format_phone_number(self.emergency_phone_2)

    def action_open_whatsapp(self):
        for employee in self:
            phone = employee.work_phone or employee.private_phone
            if phone:
                # Eliminar caracteres no numéricos
                phone = re.sub(r'\D', '', phone)
                # Verificar si el número ya tiene un código de país
                if not phone.startswith('52'):
                    phone = '52' + phone
                message = "Hola"
                url = f"https://wa.me/{phone}?text={message}"
                return {
                    'type': 'ir.actions.act_url',
                    'url': url,
                    'target': 'new',
                }
            else:
                raise UserError("The employee does not have a phone number.")
            

    def action_open_employee_documents(self):
        return {
            'name': _('Documentos del Empleado'),
            'view_type': 'form',
            'view_mode': 'kanban,list,form',
            'res_model': 'ir.attachment',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('res_model', '=', 'hr.employee'), ('res_id', '=', self.id)],
            'context': {'default_res_model': 'hr.employee', 'default_res_id': self.id, 'create': True, 'edit': True},
        }

    def action_download_employee_documents(self):
        """Genera un único PDF con todos los documentos del empleado."""
        self.ensure_one()  # Asegúrate de que solo se procese un empleado a la vez

        # Redirigir al controlador para descargar el PDF
        return {
            'type': 'ir.actions.act_url',
            'url': f'/download/employee/documents/{self.id}',
            'target': 'self',
        }

    def get_formatted_date_of_entry(self):
        """Returns the earliest date_of_entry formatted in Spanish."""
        for employee in self:
            contracts = employee.contract_ids.filtered(lambda c: c.date_of_entry)
            if contracts:
                earliest_date = min(contracts.mapped('date_of_entry'))
                return earliest_date.strftime('%d-%B-%Y').upper().replace(
                    'JANUARY', 'ENERO').replace('FEBRUARY', 'FEBRERO').replace('MARCH', 'MARZO').replace(
                    'APRIL', 'ABRIL').replace('MAY', 'MAYO').replace('JUNE', 'JUNIO').replace(
                    'JULY', 'JULIO').replace('AUGUST', 'AGOSTO').replace('SEPTEMBER', 'SEPTIEMBRE').replace(
                    'OCTOBER', 'OCTUBRE').replace('NOVEMBER', 'NOVIEMBRE').replace('DECEMBER', 'DICIEMBRE')
            return 'N/A'
        
    def get_formatted_today_date(self):
        """Returns today's date formatted in Spanish."""
        today = datetime.today()
        return today.strftime('%d de %B de %Y').upper().replace(
            'JANUARY', 'ENERO').replace('FEBRUARY', 'FEBRERO').replace('MARCH', 'MARZO').replace(
            'APRIL', 'ABRIL').replace('MAY', 'MAYO').replace('JUNE', 'JUNIO').replace(
            'JULY', 'JULIO').replace('AUGUST', 'AGOSTO').replace('SEPTEMBER', 'SEPTIEMBRE').replace(
            'OCTOBER', 'OCTUBRE').replace('NOVEMBER', 'NOVIEMBRE').replace('DECEMBER', 'DICIEMBRE')
    
    def get_nationality(self):
        translations = {
            'Mexico': 'Mexicana',
            'Colombia': 'Colombiana',
            'Argentina': 'Argentina',
            'España': 'Española',
            # Agrega más traducciones según sea necesario
        }
        country_name = self.country_id.name
        return translations.get(country_name, country_name)
    
    def action_archive_employee(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Dar de Baja al Empleado',
            'res_model': 'hr.employee.archive.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_employee_id': self.id},
        }

    # Método para reactivar
    def action_reactivate_employee(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Reactivar Empleado',
            'res_model': 'hr.employee.reactivate.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_employee_id': self.id},
        }
    
    def action_view_history(self):
        """Abre una vista modal con el historial de altas y bajas del empleado."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Historial de Altas y Bajas',
            'res_model': 'hr.employee.history',  # Modelo relacionado con el historial
            'view_mode': 'list,form',           # Vista en modo lista y formulario
            'target': 'new',                    # Abrir como modal
            'domain': [('employee_id', '=', self.id)],  # Filtrar por el empleado actual
            'context': {
                'default_employee_id': self.id,
                'create': False,  # Deshabilitar el botón "New"
            },
        }

    def action_save(self):
        self.ensure_one()

        _logger.info("Mostrando vista lista + efecto rainbow_man")

        return {
            'effect': { 
                'fadeout': 'slow',
                'message': '¡Empleado registrado exitosamente!',
                'type': 'rainbow_man',
            },
            'type': 'ir.actions.act_window',
            'res_model': self._name, 
            'view_mode': 'list',
            'target': 'current',
            
        }
    
    def _sync_codeigniter_archive(self):
        """Sincroniza el archivado del empleado con CodeIgniter"""
        api_url = self.env['ir.config_parameter'].get_param('codeigniter.api_url')
        api_token = self.env['ir.config_parameter'].get_param('codeigniter.api_token')
        
        if not api_url or not api_token:
            _logger.error("Configuración de API para CodeIgniter faltante")
            return False

        # Preparar payload
        payload = {
            'action': 'archive',
            'odoo_id': self.id,
        }

        try:
            endpoint = f"{api_url}/empleados/{self.id}/archive"
            headers = {
                'Authorization': f'Bearer {api_token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.post(
                endpoint,
                json=payload,
                headers=headers,
                timeout=30,
                verify=False
            )
            
            _logger.info(f"Respuesta CI para archivado: {response.status_code} - {response.text}")
            
            if response.status_code == 200:
                return True
            else:
                _logger.error(f"Error CI: {response.status_code} - {response.text}")
                return False
                    
        except Exception as e:
            _logger.error(f"Error de conexión con CodeIgniter: {str(e)}")
            return False

    def _sync_codeigniter_unarchive(self):
        """Sincroniza la reactivación del empleado con CodeIgniter"""
        api_url = self.env['ir.config_parameter'].get_param('codeigniter.api_url')
        api_token = self.env['ir.config_parameter'].get_param('codeigniter.api_token')
        
        if not api_url or not api_token:
            _logger.error("Configuración de API para CodeIgniter faltante")
            return False

        payload = {
            'action': 'unarchive',
            'odoo_id': self.id,
        }

        try:
            endpoint = f"{api_url}/empleados/{self.id}/unarchive"
            headers = {
                'Authorization': f'Bearer {api_token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.post(
                endpoint,
                json=payload,
                headers=headers,
                timeout=30,
                verify=False
            )
            
            _logger.info(f"Respuesta CI para reactivación: {response.status_code} - {response.text}")
            
            if response.status_code == 200:
                return True
            else:
                _logger.error(f"Error CI: {response.status_code} - {response.text}")
                return False
                    
        except Exception as e:
            _logger.error(f"Error de conexión con CodeIgniter: {str(e)}")
            return False

    # Sobrescribir métodos estándar para manejar archivado/desarchivado directo
    def action_archive(self):
        res = super(HrEmployee, self).action_archive()
        for employee in self:
            try:
                employee._sync_codeigniter_archive()
            except Exception as e:
                _logger.error(f"Error en sincronización de baja directa: {str(e)}")
        return res

    def action_unarchive(self):
        res = super(HrEmployee, self).action_unarchive()
        for employee in self:
            try:
                employee._sync_codeigniter_unarchive()
            except Exception as e:
                _logger.error(f"Error en sincronización de reactivación directa: {str(e)}")
        return res

    # Método para generar periodos de vacaciones automáticamente    
    def generate_vacation_periods(self):
        _logger.info(f"Generating vacation periods for employees: {self.ids}")
        
        employees_without_date = self.filtered(lambda e: not e.employment_start_date)
        if employees_without_date:
            raise UserError(
                "Los siguientes empleados no tienen fecha de ingreso configurada: %s" %
                ", ".join(employees_without_date.mapped('name'))
            )
        
        for employee in self:
            # Eliminar periodos existentes
            employee.vacation_period_ids.unlink()
            
            start_date = employee.employment_start_date
            today = fields.Date.today()
            periods = []
            year_count = 1
            
            while start_date < today:
                year_end = start_date + relativedelta(years=1, days=-1)
                
                # Asegurar que no exceda la fecha actual
                if year_end > today:
                    year_end = today
                    
                # Calcular días según ley mexicana actual
                if year_count == 1:
                    entitled = 12
                elif year_count == 2:
                    entitled = 14
                elif year_count == 3:
                    entitled = 16
                elif year_count == 4:
                    entitled = 18
                elif year_count == 5:
                    entitled = 20
                else:
                    # Años adicionales: +2 días por cada 5 años después del 5to
                    additional_years = year_count - 5
                    additional_days = (additional_years // 5) * 2
                    entitled = 20 + additional_days
                    
                periods.append({
                    'employee_id': employee.id,
                    'year_start': start_date,
                    'year_end': year_end,
                    'entitled_days': entitled,
                })
                
                start_date = year_end + relativedelta(days=1)
                year_count += 1
                
                # Prevenir bucles infinitos
                if year_count > 50:
                    break
            
            if periods:
                self.env['hr.vacation.period'].create(periods)
                
        # Mostrar mensaje de confirmación
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Periodos generados',
                'message': f'Se han generado {len(periods)} periodos vacacionales',
                'sticky': False,
            }
        }