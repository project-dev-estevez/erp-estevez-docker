import json
import logging
from odoo import api, models, fields, _
from odoo.exceptions import UserError, ValidationError
from datetime import date, timedelta, datetime
from dateutil.relativedelta import relativedelta
import re
import requests
import math

_logger = logging.getLogger(__name__)

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    #Campo para seleccionar el estado del catálogo
    state_id = fields.Many2one('hr.state', string="Estado", ondelete='set null')    
    state_key = fields.Char(compute='_compute_state_key', store=True)

    municipality_id = fields.Many2one('hr.municipality', string="Municipio", domain="[('state_id', '=', state_id)]", ondelete='set null')
    municipality_key = fields.Char(compute='_compute_municipality_key', store=True)

    occupation_id = fields.Many2one('hr.occupation', string="Ocupaciones", ondelete='set null')
    occupation_key = fields.Char(compute='_compute_occupation_key', store=True)    

    estudios_id = fields.Many2one('hr.estudios', string="Nivel de estudios", ondelete='set null')
    estudios_key = fields.Char(compute='_compute_estudios_key', store=True)    

    documento_id = fields.Many2one('hr.probatorio', string="Documento probatorio", ondelete='set null')
    documento_key = fields.Char(compute='_compute_documento_key', store=True)

    institucion_id = fields.Many2one('hr.institucion', string="Institución", ondelete='set null')
    institucion_key = fields.Char(compute='_compute_institucion_key', store=True)

    study_field_new = fields.Selection([
        ('administracion', 'Administración'),
        ('contaduria', 'Contaduría'),
        ('derecho', 'Derecho'),
        ('psicologia', 'Psicología'),
        ('medicina', 'Medicina'),
        ('enfermeria', 'Enfermería'),
        ('arquitectura', 'Arquitectura'),
        ('ingenieria_civil', 'Ingeniería Civil'),
        ('ingenieria_industrial', 'Ingeniería Industrial'),
        ('ingenieria_sistemas', 'Ingeniería en Sistemas Computacionales'),
        ('ingenieria_electronica', 'Ingeniería Electrónica'),
        ('ingenieria_mecanica', 'Ingeniería Mecánica'),
        ('ingenieria_quimica', 'Ingeniería Química'),
        ('biologia', 'Biología'),
        ('biotecnologia', 'Biotecnología'),
        ('mercadotecnia', 'Mercadotecnia'),
        ('comunicacion', 'Ciencias de la Comunicación'),
        ('educacion', 'Ciencias de la Educación'),
        ('pedagogia', 'Pedagogía'),
        ('sociologia', 'Sociología'),
        ('trabajo_social', 'Trabajo Social'),
        ('diseno_grafico', 'Diseño Gráfico'),
        ('diseno_industrial', 'Diseño Industrial'),
        ('turismo', 'Turismo'),
        ('gastronomia', 'Gastronomía'),
        ('ingenieria_ambiental', 'Ingeniería Ambiental'),
        ('ingenieria_en_software', 'Ingeniería en Software'),
        ('matematicas', 'Matemáticas'),
        ('fisica', 'Física'),
        ('quimica', 'Química'),
        ('veterinaria', 'Medicina Veterinaria y Zootecnia'),
        ('agronomia', 'Agronomía'),
        ('relaciones_internacionales', 'Relaciones Internacionales'),
        ('economia', 'Economía'),
        ('finanzas', 'Finanzas'),
        ('arte', 'Artes Visuales'),
        ('musica', 'Música'),
        ('teatro', 'Teatro'),
        ('filosofia', 'Filosofía'),
        ('historia', 'Historia'),
        ('ciencias_politicas', 'Ciencias Políticas'),
    ], string="Campo de estudio", help="Selecciona la carrera universitaria del empleado")

    study_tag_ids = fields.Many2many(
        'hr.study.tag', 
        'employee_skill_tag_rel', 
        'employee_id',   
        'tag_id',    
        string='Estatus académico',      
        help='Selecciona el estatus academico del empleado.',
    )




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
    #company_id = fields.Many2one('res.company', string='Company', compute='_compute_company', store=True, readonly=True)
    company_id = fields.Many2one('res.company', string='Compañía', default=lambda self: self.env.company)
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

    patron = fields.Selection([
        ('estevezjor', 'EstevezJor Servicios S.A. de C.V.'),
        ('corporativo_comunicacion', 'Corporativo en Comunicacion Digital del Futuro, S.A. de C.V.'),
        ('planta_ambientalista', 'Planta Ambientalista EESZ S.A. de C.V.'),
        ('herrajes', 'Herrajes Estevez S.A. de C.V.'),
        ('pnk', 'PNK & Ble Strategies, S.A. de C.V.'),
        ('voch', 'Voch Especialistas de México, S.A. de C.V.'),
        ('rastreo', 'Rastreo Satelital de México J&J S.A. de C.V.'),
        ('grupo_back', 'Grupo Back Bone de México S.A. de C.V.')
    ], string='Patrón Fiscal')

    establecimiento = fields.Selection([
        ('estevezjor', 'Estevez.Jor Servicios'),
        ('herrajes', 'Herrajes Estevez'),
        ('grupo_back', 'Grupo BackBone'),
        ('kuali', 'Kuali Digital'),
        ('makili', 'Makili'),
        ('vigiliner', 'Vigiliner')                
    ], string='Establecimiento')

    bank_id = fields.Many2one('res.bank', string='Banco')
    clabe = fields.Char(
        string='CLABE',
        size=18,
        help='CLABE interbancaria de 18 dígitos'
    )
    
    account_number = fields.Char(
        string='Número de Cuenta',
        help='Número de cuenta bancaria'
    )


    rfc = fields.Char(string='RFC', help='RFC de 13 dígitos', size=13)
    curp = fields.Char(string='CURP', help='CURP de 18 dígitos', size=18)
    nss = fields.Char(string='NSS', help='Número de Seguridad Social', size=11)
    voter_key = fields.Char(string='Clave Elector', size=18 )
    license_number = fields.Char(string='Número de Licencia')
    infonavit = fields.Boolean(string='Infonavit', default=False)
    private_colonia = fields.Char(string="Colonia")
    fiscal_zip = fields.Char(string="Fiscal ZIP")

    work_phone = fields.Char(string='Work Phone', compute=False)
    # coach_id = fields.Many2one('hr.employee', string='Instructor', compute=False, store=False)

    # Campo almacenado para búsquedas y referencias
    name = fields.Char(
        string='Nombre Completo',
        compute='_compute_full_name',
        inverse='_inverse_full_name',
        store=True,
        compute_sudo=True
    )

    # Campo para mostrar en vista (no almacenado)
    display_name = fields.Char(
        string='Nombre (Vista)',
        compute='_compute_display_name',
        store=False,
        compute_sudo=True
    )
    age = fields.Integer(string='Edad', compute='_compute_age')

    country_id = fields.Many2one('res.country', string='País', default=lambda self: self.env.ref('base.mx').id)
    country_of_birth = fields.Many2one('res.country', string="Country of Birth", groups="hr.group_hr_user", tracking=True, default=lambda self: self.env.ref('base.mx').id)    
    """lugar_nacimiento_estado = fields.Selection(
        selection=[
            ('aguascalientes', 'Aguascalientes'),
            ('baja_california', 'Baja California'),
            ('baja_california_sur', 'Baja California Sur'),
            ('campeche', 'Campeche'),
            ('chiapas', 'Chiapas'),
            ('chihuahua', 'Chihuahua'),
            ('ciudad_mexico', 'Ciudad de México'),
            ('coahuila', 'Coahuila'),
            ('colima', 'Colima'),
            ('durango', 'Durango'),
            ('guanajuato', 'Guanajuato'),
            ('guerrero', 'Guerrero'),
            ('hidalgo', 'Hidalgo'),
            ('jalisco', 'Jalisco'),
            ('mexico', 'Estado de México'),
            ('michoacan', 'Michoacán'),
            ('morelos', 'Morelos'),
            ('nayarit', 'Nayarit'),
            ('nuevo_leon', 'Nuevo León'),
            ('oaxaca', 'Oaxaca'),
            ('puebla', 'Puebla'),
            ('queretaro', 'Querétaro'),
            ('quintana_roo', 'Quintana Roo'),
            ('san_luis_potosi', 'San Luis Potosí'),
            ('sinaloa', 'Sinaloa'),
            ('sonora', 'Sonora'),
            ('tabasco', 'Tabasco'),
            ('tamaulipas', 'Tamaulipas'),
            ('tlaxcala', 'Tlaxcala'),
            ('veracruz', 'Veracruz'),
            ('yucatan', 'Yucatán'),
            ('zacatecas', 'Zacatecas')
        ],
        string='Lugar de Nacimiento',
        help='Selecciona el estado de nacimiento del empleado'
    )"""
    private_country_id = fields.Many2one("res.country", string="Private Country", groups="hr.group_hr_user", default=lambda self: self.env.ref('base.mx').id)
    is_mexico = fields.Boolean(string="Is Mexico", compute="_compute_is_mexico", store=False)

    marital = fields.Selection([
        ('single', 'Soltero(a)'),
        ('married', 'Casado(a)'),
        ('cohabitant', 'Unión libre'),
        ('widower', 'Viudo(a)'),
        ('divorced', 'Divorciado(a)')
    ], string='Estado Civil', required=True, tracking=True)

    spouse_name = fields.Char(string="Nombre del cónyuge")

    spouse_birthdate = fields.Date(string="Spouse Birthdate", groups="hr.group_hr_user", store=False)

    memorandum_ids = fields.One2many('hr.memorandum', 'employee_id', string='Actas Administrativas')
    loan_ids = fields.One2many('hr.loan', 'employee_id', string='Préstamos y Anticipos')

    vacation_period_ids = fields.One2many(
        'hr.vacation.period', 'employee_id', string="Periodos de Vacaciones"
    )

    #emergency_contact_relationship = fields.Char(string="Parentesco del Primer Contacto")
    emergency_contact_relationship = fields.Selection([
        ('mom', 'Madre'),
        ('dad', 'Padre'),
        ('daughter', 'Hijo(a)'),
        ('couple', 'Esposo(a)'),
        ('brother/sister', 'Hermano(a)'),
        ('other', 'Otro')
    ], string='Estado Civil', tracking=True)
    
    # Campos para el segundo contacto de emergencia
    emergency_contact_2 = fields.Char(string="Segundo Contacto")
    emergency_contact_relationship_2 = fields.Selection([
        ('mom', 'Madre'),
        ('dad', 'Padre'),
        ('daughter', 'Hijo(a)'),
        ('couple', 'Esposo(a)'),
        ('brother/sister', 'Hermano(a)'),
        ('other', 'Otro')
    ], string='Estado Civil', tracking=True)
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

    leave_ids = fields.One2many('hr.leave', 'period_id')

    ir_attachment_count = fields.Integer(
        string="Cantidad de Documentos",
        compute="_compute_ir_attachment_count"
    )

    time_off_in_lieu_ids = fields.One2many(
        'hr.time.off.in.lieu', 
        'employee_id', 
        string='Solicitudes de Tiempo por Tiempo'
    )

    job_history_ids = fields.One2many(
        'hr.employee.job.history',
        'employee_id',
        string="Historial de puestos"
    )

    
    def _compute_ir_attachment_count(self):
        for employee in self:
            employee.ir_attachment_count = self.env['ir.attachment'].search_count([
                ('res_model', '=', 'hr.employee'),
                ('res_id', '=', employee.id)
            ])

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
            
    @api.model_create_multi
    def create(self, vals_list):
        _logger.info("=== CREATE EMPLOYEE ===")
        
        for vals in vals_list:
            # CALCULAR EL NOMBRE COMPLETO AQUÍ
            names = vals.get('names', '').strip()
            last_name = vals.get('last_name', '').strip()
            mother_last_name = vals.get('mother_last_name', '').strip()
            
            parts = []
            for part in (names, last_name, mother_last_name):
                if part:
                    parts.append(part)
            
            full_name = ' '.join(parts) if parts else ''
            vals['name'] = full_name  # ESTABLECER name DIRECTAMENTE
            
            _logger.info(f"CREATE: names={names}, last={last_name}, mother={mother_last_name}, name={full_name}")
            
            # Sincronización de barcode/employee_number
            if 'employee_number' in vals and vals['employee_number'] and not vals.get('barcode'):
                vals['barcode'] = vals['employee_number']
            elif 'barcode' in vals and vals['barcode'] and not vals.get('employee_number'):
                vals['employee_number'] = vals['barcode']
            
            if not vals.get('employee_number'):
                company_id = vals.get('company_id', self.env.company.id)
                next_number = self._get_next_employee_number(company_id)
                vals['employee_number'] = next_number
                if not vals.get('barcode'):
                    vals['barcode'] = next_number
        
        employees = super(HrEmployee, self).create(vals_list)
        
        # Acciones post-creación
        for employee in employees:
            if employee.employment_start_date:
                try:
                    employee.generate_vacation_periods()
                except Exception as e:
                    _logger.error(f"Error generando períodos: {str(e)}")
            
            try:
                employee._sync_codeigniter(employee, 'create')
            except Exception as e:
                _logger.error(f"Error en sincronización: {str(e)}")
        
        return employees


    def write(self, vals):
        _logger.info(f"=== WRITE EMPLOYEE {self.ids} ===")
        _logger.info(f"Valores a escribir: {vals}")
        
        # Calcular nuevo nombre si se actualizan campos relacionados
        if any(field in vals for field in ['names', 'last_name', 'mother_last_name']):
            for rec in self:
                # Obtener valores nuevos o actuales
                names = vals.get('names', rec.names or '')
                last_name = vals.get('last_name', rec.last_name or '')
                mother_last_name = vals.get('mother_last_name', rec.mother_last_name or '')
                
                # Calcular nombre completo
                parts = []
                for part in (names, last_name, mother_last_name):
                    if part and str(part).strip():
                        parts.append(str(part).strip())
                
                new_name = ' '.join(parts) if parts else ''
                
                # Agregar a valores a escribir
                if 'name' not in vals:
                    vals['name'] = new_name
                
                _logger.info(f"WRITE CALCULATION: names={names}, last={last_name}, mother={mother_last_name}, new_name={new_name}")
                break  # Solo necesitamos calcular para el primer registro
        
        # Sincronizar barcode
        if 'employee_number' in vals and 'barcode' not in vals:
            vals['barcode'] = vals['employee_number']
        elif 'barcode' in vals and 'employee_number' not in vals:
            vals['employee_number'] = vals['barcode']
        
        # Resto de la lógica (historial, vacaciones, etc.)
        if 'job_id' in vals:
            for rec in self:
                new_job_id = vals.get('job_id')
                if isinstance(new_job_id, (list, tuple)):
                    new_job_id = new_job_id[0]
                if rec.job_id.id != new_job_id:
                    self.env['hr.employee.job.history'].create({
                        'employee_id': rec.id,
                        'old_job_id': rec.job_id.id,
                        'new_job_id': new_job_id,
                        'changed_by': self.env.user.id,
                        'change_date': fields.Datetime.now(),
                    })
        
        if 'employment_start_date' in vals:
            for employee in self:
                if not vals['employment_start_date']:
                    employee.vacation_period_ids.unlink()
                    continue
                if any(period.days_taken > 0 for period in employee.vacation_period_ids):
                    raise UserError("No se puede cambiar la fecha de ingreso porque hay días de vacaciones ya tomados.")
                employee.vacation_period_ids.unlink()
        
        # Ejecutar write
        res = super().write(vals)
        
        # Acciones post-write
        if 'employment_start_date' in vals:
            for employee in self:
                if employee.employment_start_date:
                    employee.generate_vacation_periods()
        
        try:
            for employee in self:
                employee._sync_codeigniter(employee, 'update')
        except Exception as e:
            _logger.error(f"Error en sincronización: {str(e)}")
        
        return res
    

    def generate_random_barcode(self):
        
        for employee in self:
            # Llamar al método original para generar el barcode
            super(HrEmployee, employee).generate_random_barcode()
            
            # Sincronizar employee_number con el barcode generado
            if employee.barcode and not employee.employee_number:
                employee.employee_number = employee.barcode

    @api.depends('state_id')
    def _compute_state_key(self):
        for employee in self:            
            employee.state_key = employee.state_id.code if employee.state_id else False            

    @api.depends('municipality_id')
    def _compute_municipality_key(self):
        for employee in self:            
            employee.municipality_key = employee.municipality_id.code if employee.municipality_id else False  

    @api.depends('occupation_id')
    def _compute_occupation_key(self):
        for employee in self:            
            employee.occupation_key = employee.occupation_id.code if employee.occupation_id else False  

    @api.depends('estudios_id')
    def _compute_estudios_key(self):
        for employee in self:            
            employee.estudios_key = employee.estudios_id.code if employee.estudios_id else False 
            
                      
    @api.depends('documento_id')
    def _compute_documento_key(self):
        for employee in self:            
            employee.documento_key = employee.documento_id.code if employee.documento_id else False 

    @api.depends('institucion_id')
    def _compute_institucion_key(self):
        for employee in self:            
            employee.institucion_key = employee.institucion_id.code if employee.institucion_id else False 

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
    def _compute_display_name(self):
        """Para mostrar en tiempo real en la vista"""
        for rec in self:
            parts = []
            for part in (rec.names, rec.last_name, rec.mother_last_name):
                if part and str(part).strip():
                    parts.append(str(part).strip())
            rec.display_name = ' '.join(parts) if parts else ''
            _logger.info(f"DISPLAY_NAME: {rec.display_name}")

    @api.depends('names', 'last_name', 'mother_last_name')
    def _compute_full_name(self):
        """Para almacenar en la base de datos"""
        for rec in self:
            # Si ya tiene un valor, no recalcular (evita conflicto)
            if rec.name and not rec._origin:
                _logger.info(f"SKIP COMPUTE: name ya tiene valor: {rec.name}")
                continue
                
            parts = []
            for part in (rec.names, rec.last_name, rec.mother_last_name):
                if part and str(part).strip():
                    parts.append(str(part).strip())
            result = ' '.join(parts) if parts else ''
            
            # Solo asignar si es diferente
            if rec.name != result:
                rec.name = result
                _logger.info(f"COMPUTE_FULL_NAME asignado: {result}")

    def _inverse_full_name(self):
        """
        Inverse method para permitir escritura directa en 'name'
        No es necesario implementar si no quieres editar directamente
        """
        pass

    def debug_name_problem(self):
        """Método para diagnosticar el problema del nombre"""
        self.ensure_one()
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Debug del Nombre',
                'message': f'''
                Nombres: {self.names or "(vacío)"}
                Apellido Paterno: {self.last_name or "(vacío)"}
                Apellido Materno: {self.mother_last_name or "(vacío)"}
                Nombre en BD (name): {self.name or "(vacío)"}
                Nombre en Vista (display_name): {self.display_name or "(vacío)"}
                
                ¿Son iguales? {"SÍ" if self.name == self.display_name else "NO"}
                ''',
                'type': 'warning',
                'sticky': True,
            }
        }

    @api.onchange('names', 'last_name', 'mother_last_name')
    def _onchange_name_fields(self):
        """Forzar actualización inmediata en la vista"""
        for rec in self:
            # Forzar cálculo de ambos campos
            rec._compute_display_name()
            rec._compute_full_name()
            _logger.info(f"ONCHANGE: names={rec.names}, last={rec.last_name}, mother={rec.mother_last_name}, name={rec.name}")

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


    def _get_next_employee_number(self, company_id=False):
        """Obtener el siguiente número de empleado por empresa"""
        # Si no se proporciona company_id, usar la compañía actual del entorno
        if not company_id:
            company_id = self.env.company.id

        # Buscar el último empleado por empresa
        last_employee = self.search([
            ('company_id', '=', company_id),
            ('employee_number', '!=', False)
        ], order='id desc', limit=1)

        if last_employee and last_employee.employee_number:
            # Intentar extraer el número y incrementar
            try:
                # Asumimos que el employee_number es un string numérico
                last_number = int(last_employee.employee_number)
                next_number = last_number + 1
            except (ValueError, TypeError):
                # Si no es numérico, empezar desde 1
                next_number = 1
        else:
            # Primer empleado en la empresa
            next_number = 1

        # Formatear con ceros a la izquierda (5 dígitos)
        return str(next_number).zfill(5)
    
    def generate_random_barcode(self):
        """Sobrescribir el método de generar barcode para usar nuestro número por empresa"""
        for employee in self:
            if not employee.employee_number:
                next_number = self._get_next_employee_number(employee.company_id.id)
                employee.write({
                    'employee_number': next_number,
                    'barcode': next_number
                })
            else:
                # Si ya tiene número, sincronizar
                employee.barcode = employee.employee_number
        
        # Mostrar notificación
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Número Generado',
                'message': f'Número de empleado generado: {self.employee_number}',
                'type': 'success',
                'sticky': False,
            }
        }
    
    def action_sync_employee_numbers(self):
        """Acción para sincronizar todos los números existentes"""
        employees = self.search([])
        for employee in employees:
            if employee.employee_number and not employee.barcode:
                employee.barcode = employee.employee_number
            elif employee.barcode and not employee.employee_number:
                employee.employee_number = employee.barcode
        
        _logger.info(f"Sincronizados {len(employees)} empleados")
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Sincronización Completada',
                'message': f'Se han sincronizado {len(employees)} empleados',
                'type': 'success',
                'sticky': False,
            }
        }
    
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
    
    def action_create_user(self):
        """
        Valida que el empleado tenga email corporativo o employee_number
        antes de permitir la creación del usuario.
        
        Flujos:
        - Con work_email: Invitación por correo (flujo normal Odoo)
        - Sin work_email (solo employee_number): Contraseña por defecto con cambio obligatorio
        """
        self.ensure_one()
        
        # Validar si ya tiene usuario
        if self.user_id:
            raise ValidationError(_("This employee already has an user."))
        
        has_email = bool(self.work_email)
        has_employee_number = bool(self.employee_number)

        context = dict(self._context)
        
        # Validación: debe tener al menos uno de los dos campos
        if not has_email and not has_employee_number:
            raise UserError(_(
                '❌ NO SE PUEDE CREAR EL USUARIO\n\n'
                'El empleado "%s" necesita al menos UNO de los siguientes campos:\n\n'
                '  ✓ Correo Corporativo (Email de Trabajo)\n'
                '  ✓ Número de Empleado\n\n'
                '📝 Por favor complete alguno de estos campos e intente nuevamente.'
            ) % self.name)
        
        if not has_email:
            # Sin email: marcar para contraseña por defecto + cambio obligatorio
            context['default_no_email_employee'] = True
            context['no_reset_password'] = True  # Evitar envío de email
            
            _logger.info(
                f"🔐 Usuario {self.name} (ID: {self.id}) será creado SIN EMAIL - "
                f"Se asignará contraseña temporal '12345678' con cambio obligatorio en primer login"
            )
        else:
            # Con email: flujo normal de invitación
            context['no_reset_password'] = False
            
            _logger.info(
                f"📧 Usuario {self.name} (ID: {self.id}) será creado CON EMAIL - "
                f"Se enviará invitación a: {self.work_email}"
            )
        
        _logger.info(
            f"Creando usuario para empleado {self.name} (ID: {self.id}) - "
            f"Email: {has_email}, Número: {has_employee_number}"
        )
        
        # Retornar acción del wizard con contexto prellenado
        return {
            'name': _('Create User'),
            'type': 'ir.actions.act_window',
            'res_model': 'res.users',
            'view_mode': 'form',
            'view_id': self.env.ref('base.view_users_simple_form').id,
            'target': 'new',
            'context': dict(context, **{
                'default_create_employee_id': self.id,
                'default_name': self.name,
                'default_phone': self.work_phone,
                'default_mobile': self.mobile_phone,
                'default_login': self.work_email or self.employee_number,
                'default_partner_id': self.work_contact_id.id,
            })
        }

    def action_open_employee_documents(self):
        self.ensure_one()
        self.env['hr.employee.document'].search([('employee_id', '=', self.id)]).unlink()
        self.env['hr.employee.document'].create_required_documents(self.id)
        return {
            'name': _('Documentos del Empleado'),
            'view_mode': 'kanban',
            'res_model': 'hr.employee.document',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {'create': False},
            'domain': [('employee_id', '=', self.id)],
            'views': [(self.env.ref('hr_estevez.view_hr_employee_documents_kanban').id, 'kanban')],
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
        self.ensure_one()  # Asegura que solo se actúa sobre un registro
        return {
            'type': 'ir.actions.act_window',
            'name': 'Dar de Baja al Empleado',
            'res_model': 'hr.employee.archive.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_employee_id': self.id},
        }

    def action_reactivate_employee(self):
        self.ensure_one()
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
        _logger.info(f"Archivando empleados: {self.ids}")
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

        effective_new_law = fields.Date.from_string('2022-01-01')
        total_created = 0

        for employee in self:
            employee.vacation_period_ids.unlink()

            start_date = employee.employment_start_date
            today = fields.Date.today()
            periods = []
            year_count = 1

            while start_date < today:
                # Calcular fin de año natural
                year_end_full = start_date + relativedelta(years=1, days=-1)
                
                # Determinar si es el período actual
                is_current_period = year_end_full >= today
                period_end = today if is_current_period else year_end_full

                # Determinar días de vacaciones según ley
                under_new_law = start_date >= effective_new_law
                entitled_full = self._calculate_entitled_days(year_count, under_new_law)

                # Si es el período actual, calcular proporcional
                if is_current_period:
                    entitled_days = self._calculate_proportional_days(
                        start_date, period_end, entitled_full, year_count
                    )
                else:
                    entitled_days = entitled_full

                periods.append({
                    'employee_id': employee.id,
                    'year_start': start_date,
                    'year_end': period_end,
                    'entitled_days': entitled_days,
                })

                # Avanzar al siguiente período si no es el actual
                if not is_current_period:
                    start_date = period_end + relativedelta(days=1)
                    year_count += 1
                else:
                    break

                if year_count > 50:  # Límite de seguridad
                    break

            if periods:
                self.env['hr.vacation.period'].create(periods)
                total_created += len(periods)

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Periodos generados',
                'message': f'Se han generado {total_created} periodos vacacionales',
                'sticky': False,
            }
        }

    def _calculate_entitled_days(self, year_count, under_new_law):
        """Calcular días de vacaciones según años de servicio y ley aplicable"""
        if not under_new_law:
            # Ley antigua
            if year_count == 1:
                return 6
            elif year_count == 2:
                return 8
            elif year_count == 3:
                return 10
            elif year_count == 4:
                return 12
            elif year_count == 5:
                return 14
            else:
                return 16
        else:
            # Nueva ley
            if year_count == 1:
                return 12
            elif year_count == 2:
                return 14
            elif year_count == 3:
                return 16
            elif year_count == 4:
                return 18
            elif year_count == 5:
                return 20
            else:
                additional_blocks = math.ceil((year_count - 5) / 5.0)
                return 20 + (additional_blocks * 2)

    def _calculate_proportional_days(self, start_date, end_date, entitled_full, year_count):
        """Calcular días proporcionales para el período actual"""
        # Calcular días trabajados en el período
        days_worked = (end_date - start_date).days + 1
        
        # Calcular días totales del período completo (1 año)
        full_period_end = start_date + relativedelta(years=1, days=-1)
        days_in_full_period = (full_period_end - start_date).days + 1
        
        # Evitar división por cero
        if days_in_full_period == 0:
            return 0
        
        # Calcular proporcional
        proportional_days = (entitled_full * days_worked) / days_in_full_period
        
        # Redondear según política de la empresa
        # Opción 1: Redondear al medio día más cercano
        rounded_days = math.ceil(proportional_days * 2) / 2
        
        # Opción 2: Redondear al día completo más cercano (comenta la línea anterior y descomenta esta)
        # rounded_days = round(proportional_days)
        
        # Mínimo 0.5 días si ha trabajado al menos un día
        return max(0.5, rounded_days) if days_worked > 0 else 0

    def action_create_vacation(self):
        """Abrir wizard para crear solicitud de vacaciones"""
        self.ensure_one()
        
        # Verificar que tenga días disponibles
        if self.vacation_days_available <= 0:
            raise UserError("El empleado no tiene días de vacaciones disponibles.")
        
        # Buscar el tipo de ausencia para vacaciones
        leave_type = self.env['hr.leave.type'].search([
            ('name', 'ilike', 'Vacaciones'),
            ('is_vacation', '=', 'true')
        ], limit=1)
        
        if not leave_type:
            # Si no existe, crear uno
            leave_type = self.env['hr.leave.type'].create({
                'name': 'Vacaciones',
                'requires_allocation': 'yes',
                'color_name': 'lightblue',
            })
        
        # Crear y devolver la acción del wizard
        return {
            'type': 'ir.actions.act_window',
            'name': 'Solicitar Vacaciones',
            'res_model': 'hr.leave',
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'default_employee_id': self.id,
                'default_holiday_status_id': leave_type.id,
                'default_state': 'confirm',
            }
        }
    
    def action_create_time_off_in_lieu(self):
        """Acción para crear nueva solicitud de Tiempo por Tiempo desde el empleado"""
        self.ensure_one()
        
        # Verificar que exista un tipo de ausencia para TXT
        time_off_type = self.env['hr.leave.type'].search([
            ('is_time_off_in_lieu', '=', True)
        ], limit=1)
        
        if not time_off_type:
            raise UserError("""
                No se encontró un tipo de ausencia configurado para Tiempo por Tiempo.
                Por favor, vaya a:
                Tiempo → Configuración → Tipos de Ausencias
                y marque la casilla 'Es Tiempo por Tiempo' en un tipo de ausencia.
            """)
        
        # Crear el registro de Tiempo por Tiempo
        txt_vals = {
            'name': f'TXT - {self.name} - Nueva Solicitud',
            'employee_id': self.id,
            'request_date': fields.Date.today(),
            'state': 'draft',
        }
        
        # Abrir formulario de creación
        return {
            'type': 'ir.actions.act_window',
            'name': 'Nueva Solicitud de Tiempo por Tiempo',
            'res_model': 'hr.time.off.in.lieu',
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'default_employee_id': self.id,
                'default_name': f'TXT - {self.name} - {fields.Date.today()}',
                'default_state': 'draft',
                'create': True,
            }
        }
    
    def action_view_time_off_in_lieu(self):
        """Ver todas las solicitudes de TXT del empleado"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Solicitudes de Tiempo por Tiempo',
            'res_model': 'hr.time.off.in.lieu',
            'view_mode': 'tree,form',
            'domain': [('employee_id', '=', self.id)],
            'context': {'default_employee_id': self.id},
        }
