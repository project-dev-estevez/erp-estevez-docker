import json
import logging
from odoo import api, models, fields, _
from odoo.exceptions import UserError
from datetime import date, timedelta, datetime
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
    last_name = fields.Char(string='Apellido Paterno')
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

    years_of_service = fields.Float(
        string="Años de Servicio",
        compute="_compute_years_of_service",
        store=False
    )
    entitled_days = fields.Float(
        string="Con Derecho a",
        compute="_compute_vacation_days",
        store=False
    )
    vacation_days_taken = fields.Float(
        string="Días de Vacaciones Disfrutados",
        compute="_compute_vacation_days_taken",
        store=False
    )
    vacation_days_available = fields.Float(
        string="Días de Vacaciones Disponibles",
        compute="_compute_vacation_days_available",
        store=False
    )

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

    @api.depends('contract_ids.date_start', 'contract_ids.date_end', 'years_of_service')
    def generate_vacation_periods(self):
        for employee in self:
            # Eliminar periodos existentes
            employee.vacation_period_ids.unlink()

            # Verificar si hay contratos
            if not employee.contract_ids:
                continue

            # Buscar el contrato con la fecha de inicio más antigua
            base_contract = min(employee.contract_ids, key=lambda c: c.date_start)

            # Usar la fecha de inicio del contrato base
            current_start_date = base_contract.date_start
            current_end_date = base_contract.date_end or date.today()

            # Generar periodos de vacaciones desde la fecha de inicio hasta la fecha actual
            while current_start_date <= current_end_date:
                # Calcular el fin del periodo basado en el año calendario
                year_end = current_start_date.replace(year=current_start_date.year + 1) - timedelta(days=1)
                if year_end > current_end_date:
                    year_end = current_end_date

                # Calcular años de servicio
                years_of_service = current_start_date.year - base_contract.date_start.year

                # Calcular días de vacaciones según los años de servicio
                entitled_days_full_year = 12 + (years_of_service * 2) if years_of_service < 5 else 22

                # Si es el último período, calcular proporcionalmente los días de vacaciones
                if year_end == current_end_date:
                    days_in_year = (year_end - current_start_date).days + 1
                    entitled_days = (entitled_days_full_year / 365) * days_in_year
                else:
                    entitled_days = entitled_days_full_year

                days_taken = 0  # Inicialmente 0

                # Crear el periodo de vacaciones
                self.env['hr.vacation.period'].create({
                    'employee_id': employee.id,
                    'year_start': current_start_date,
                    'year_end': year_end,
                    'entitled_days': round(entitled_days, 2),  # Redondear a 2 decimales
                    'days_taken': days_taken,
                })

                # Avanzar al siguiente año
                current_start_date = current_start_date.replace(year=current_start_date.year + 1)

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

    @api.depends('contract_ids.date_start', 'contract_ids.date_end', 'contract_ids.state')
    def _compute_years_of_service(self):
        for employee in self:
            total_days = 0
            today = date.today()

            # Iterar sobre todos los contratos del empleado
            for contract in employee.contract_ids:
                # Considerar solo contratos en estado 'open' o 'close'
                if contract.date_start:
                    # Si el contrato tiene fecha de fin, usarla; de lo contrario, usar la fecha actual
                    end_date = contract.date_end or today
                    total_days += (end_date - contract.date_start).days

            # Convertir días totales en años decimales
            employee.years_of_service = round(total_days / 365.0, 2)

    @api.depends('years_of_service')
    def _compute_vacation_days(self):
        for employee in self:
            years = int(employee.years_of_service)  # Convertir años de servicio a entero
            entitled_days = 0

            # Calcular días de vacaciones acumulativos según los años laborados
            if years >= 1:
                for i in range(1, years + 1):
                    if i == 1:
                        entitled_days += 12
                    elif i == 2:
                        entitled_days += 14
                    elif i == 3:
                        entitled_days += 16
                    elif i == 4:
                        entitled_days += 18
                    elif i == 5:
                        entitled_days += 20
                    elif 6 <= i <= 10:
                        entitled_days += 22
                    elif 11 <= i <= 15:
                        entitled_days += 24
                    elif 16 <= i <= 20:
                        entitled_days += 26
                    elif 21 <= i <= 25:
                        entitled_days += 28
                    elif 26 <= i <= 30:
                        entitled_days += 30
                    elif 31 <= i <= 50:
                        entitled_days += 32

            # Asignar los días calculados al campo
            employee.entitled_days = entitled_days

    @api.depends('entitled_days')
    def _compute_vacation_days_taken(self):
        for employee in self:
            # Inicializar el campo con 0
            employee.vacation_days_taken = 0

            # Obtener los días de vacaciones aprobados para el empleado
            leaves = self.env['hr.leave'].search([
                ('employee_id', '=', employee.id),
                ('state', '=', 'validate')  # Solo considerar vacaciones aprobadas
            ])

            # Sumar los días de vacaciones aprobados
            if leaves:
                employee.vacation_days_taken = sum(leaves.mapped('number_of_days'))

    @api.depends('entitled_days', 'vacation_days_taken')
    def _compute_vacation_days_available(self):
        for employee in self:
            # Calcular los días disponibles
            employee.vacation_days_available = employee.entitled_days - employee.vacation_days_taken

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
            vals['name'] = f"{names} {vals.get('last_name', '')} {vals.get('mother_last_name', '')}".strip()
        
        # Crear empleado
        employee = super(HrEmployee, self).create(vals)
        
        # Lógica de dirección
        if 'direction_id' in vals and vals['direction_id']:
            direction = self.env['hr.direction'].browse(vals['direction_id'])
            direction.director_id = employee.id
        
        # Sincronizar con CodeIgniter (sin bloquear en caso de error)
        try:
            _logger.info("Intentando sincronizar con CodeIgniter")
            self._sync_codeigniter(employee, 'create')
        except Exception as e:
            _logger.error(f"Error en sincronización: {str(e)}")
        
        return employee

    def write(self, vals):
       
        if 'name' not in vals and ('names' in vals or 'last_name' in vals or 'mother_last_name' in vals):
            # Obtener valores de forma segura (convertir a string)
            names_val = str(vals.get('names', self.names)) if vals.get('names', self.names) is not False else ''
            last_name_val = str(vals.get('last_name', self.last_name)) if vals.get('last_name', self.last_name) is not False else ''
            mother_last_name_val = str(vals.get('mother_last_name', self.mother_last_name)) if vals.get('mother_last_name', self.mother_last_name) is not False else ''
            
            # Construir nombre completo
            full_name = f"{names_val} {last_name_val} {mother_last_name_val}".strip()
            
        vals['name'] = self.name
        
        # Resto de tu lógica para direction_id...
        for record in self:
            if 'direction_id' in vals:
                if record.direction_id:
                    old_direction = self.env['hr.direction'].browse(record.direction_id.id)
                    old_direction.director_id = False

                if vals['direction_id']:
                    new_direction = self.env['hr.direction'].browse(vals['direction_id'])
                    new_direction.director_id = record.id

        res = super().write(vals)
        
        try:
            _logger.info(f"Iniciando sincronización de actualización para {self.name}")
            self._sync_codeigniter(self, 'update')
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