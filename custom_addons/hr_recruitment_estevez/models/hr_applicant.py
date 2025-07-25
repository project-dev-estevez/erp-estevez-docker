from odoo import models, api, fields, _
from odoo.exceptions import UserError
from datetime import timedelta, date
import werkzeug
import logging
import re

_logger = logging.getLogger(__name__)

class HrApplicant(models.Model):
    _inherit = 'hr.applicant'
    
    
    is_examen_medico = fields.Boolean(compute="_compute_is_examen_medico")

    # *********Formulario de historia clinica *********
    # Ficha de Identificación
    interrogation_type = fields.Selection([('direct', 'Directo'), ('indirect', 'Indirecto')], string="Tipo de Interrogatorio")
    patient_name = fields.Char(string="Nombre del Paciente", compute="_compute_patient_name")
    gender = fields.Selection([('male', 'Masculino'), ('female', 'Femenino')], string="Género")
    birth_date = fields.Date(string="Fecha de Nacimiento")
    age = fields.Char(string="Edad", compute="_compute_age", readonly=True)
    job_position = fields.Char(string="Puesto de Trabajo", compute="_compute_job_position")
    degree_id = fields.Many2one('hr.recruitment.degree', string="Escolaridad")
    address = fields.Text(string="Dirección")
    phone = fields.Char(string="Teléfono", compute="_compute_phone")

    # Antecedentes Heredo Familiares
    family_medical_history = fields.Text(string="Antecedentes Heredo Familiares")

    # Antecedentes Personales No Patológicos
    place_of_origin = fields.Char(string="Lugar de Origen")
    place_of_residence = fields.Char(string="Lugar de Residencia")
    marital_status = fields.Selection([
        ('single', 'Soltero(a)'),
        ('married', 'Casado(a)'),
        ('cohabitant', 'En Concubinato'),
        ('widower', 'Viudo(a)'),
        ('divorced', 'Divorciado(a)')
    ], string='Estado Civil', tracking=True)
    religion = fields.Char(string="Religión")
    housing_type = fields.Selection([('own', 'Propia'), ('rented', 'Rentada')], string="Tipo de Vivienda")
    construction_material = fields.Selection([('durable', 'Durable'), ('non_durable', 'No Durable')], string="Material de Construcción", default='durable')
    housing_services = fields.Selection([
        ('intradomiciliarios', 'Intradomiciliarios'),
        ('extradomiciliarios', 'Extradomiciliarios'),
        ('intra_extradomiciliarios', 'Intra y Extradomiciliarios')
    ], string="Servicios de Vivienda")
    weekly_clothing_change = fields.Char(string="Cambio de Ropa Semanal")
    occupations = fields.Text(string="Oficios Desempeñados")
    daily_teeth_brushing = fields.Integer(string="Cepillado de Dientes Diario")
    zoonosis = fields.Selection([('negative', 'Negativo'), ('positive', 'Positivo')], string="Zoonosis")
    pet = fields.Char(string="Mascota", readonly=False)
    
    overcrowding = fields.Selection([('negative', 'Negativo'), ('positive', 'Positivo')], string="Hacinamiento")
    tattoos_piercings = fields.Selection(
        [('negative', 'Negativo'), ('positive', 'Positivo')],
        string="Tatuajes y Perforaciones"
    )
    tattoos_number = fields.Integer(
        string="Número de Tatuajes",
        readonly=False
    )

    blood_type = fields.Char(string="Tipo de Sangre")
    donor = fields.Boolean(string="Donador")

    # Antecedentes Personales Patológicos
    # Esquema de Vacunación
    complete_schedule = fields.Selection([('yes', 'Sí'), ('no', 'No')], string="Esquema Completo Vacunación")
    comments = fields.Text(string="Comentarios")
    no_vaccination_card = fields.Boolean(string="Sin Cartilla de Vacunación")
    last_vaccine = fields.Date(string="Última Vacuna")
    previous_surgeries = fields.Char(string="Quirúrgicos")
    traumas = fields.Char(string="Traumáticos")
    transfusions = fields.Char(string="Transfusionales")
    allergies = fields.Char(string="Alérgicos")
    chronic_diseases = fields.Char(string="Crónico-degenerativos")
    childhood_diseases = fields.Char(string="Enfermedades de la Infancia")
    smoking = fields.Selection([('yes', 'Sí'), ('no', 'No'), ('social', 'Social')], string="Tabaquismo")
    alcoholism = fields.Selection([('yes', 'Sí'), ('no', 'No'), ('social', 'Social')], string="Alcoholismo")
    drug_addiction = fields.Selection([('yes', 'Sí'), ('no', 'No'), ('social', 'Social')], string="Toxicomanías")

    # Antecedentes Gineco-Obstétricos
    menarche = fields.Char(string="Menarca")
    thelarche = fields.Char(string="Telarca")
    rhythm = fields.Char(string="Ritmo")
    gpca = fields.Char(string="GPCA")
    breastfeeding_history = fields.Selection([('yes', 'Sí'), ('no', 'No')], string="Antecedente de Lactancia Materna")
    ivsa = fields.Char(string="IVSA")
    nps = fields.Char(string="NPS")
    mpf = fields.Char(string="MPF")

    # Padecimiento Actual
    current_condition = fields.Text(string="Padecimiento Actual")

    # Interrogatorio por aparatos y sistemas
    cardiovascular = fields.Char(string="Cardiovascular")
    respiratory = fields.Char(string="Respiratorio")
    gastrointestinal = fields.Char(string="Gastrointestinal")
    genitourinary = fields.Char(string="Genitourinario")
    endocrine = fields.Char(string="Endocrino")
    nervous = fields.Char(string="Nervioso")
    musculoskeletal = fields.Char(string="Músculo-Esquelético")
    skin_mucous = fields.Char(string="Piel y Mucosas")

    # Signos Vitales
    heart_rate = fields.Integer(string="Frecuencia Cardiaca (Lpm)")
    respiratory_rate = fields.Integer(string="Frecuencia Respiratoria (Rpm)")
    temperature = fields.Float(string="Temperatura (°C)")
    blood_pressure = fields.Char(string="Tensión Arterial (mmHg)")
    oxygen_saturation = fields.Float(string="Saturación O2 (%)")
    weight = fields.Float(string="Peso (Kg)")
    height = fields.Float(string="Talla (Cm)")
    bmi = fields.Float(string="IMC", compute="_compute_bmi", readonly=True)

    # Exploración Física
    head_neck = fields.Char(string="Cabeza y Cuello")
    chest = fields.Char(string="Tórax")
    abdomen = fields.Char(string="Abdomen")
    extremities = fields.Char(string="Extremidades")
    neurological = fields.Char(string="Neurológico")
    skin = fields.Char(string="Piel")

    # Resultados Previos y Actuales de Laboratorio, Gabinete y Otros
    laboratory_results = fields.Text(string="Resultados")

    # Diagnóstico o Problemas Clínicos
    diagnosis = fields.Text(string="Diagnóstico")

    # Terapéutica Empleada y Resultados Previos
    previous_treatment = fields.Text(string="Terapéutica Empleada y Resultados Previos")

    # Tratamiento e Indicaciones
    treatment_recommendations = fields.Text(
        string="Tratamiento e Indicaciones",
        compute="_compute_treatment_recommendations",
        readonly=True,
        store=False
    )

    # Próxima Cita
    next_appointment = fields.Text(string="Próxima Cita")

    # Pronóstico
    prognosis = fields.Text(string="Pronóstico")

    aptitude_state = fields.Selection([
        ('apto', 'Apto'),
        ('no_apto', 'No Apto'),
        ('apto_condicionado', 'Apto Condicionado')
    ], string="Estado de Aptitud", default='apto')

    documents_count = fields.Integer(
        'Documents Count', 
        compute="_compute_applicant_documents"
    )
    
    user_id = fields.Many2one(
        'res.users',
        string="Reclutador",
        default=lambda self: self.env.user,  # Asigna el usuario logueado por defecto
    )

    project_id = fields.Many2one(
        'project.project',
        string='Proyecto',
        help='Proyecto para el que se postula el candidato'
    )

    source_id = fields.Many2one(
        'utm.source',        
        required = True,
        string='Fuente de reclutamiento',
        help='Fuente de reclutamiento',
        ondelete='restrict'       
    )

    process_duration = fields.Char(
        string='Duración',
        compute='_compute_process_duration',
        store=False
    )

    # Sobrescribir el campo candidate_id para cambiar su etiqueta
    candidate_id = fields.Many2one(
        'hr.candidate', 
        required=True, 
        index=True,
        string='Candidato',  # Cambiar el string que se muestra
        help='Candidato asociado a esta solicitud'
    )

    # === NUEVO CAMPO PARA HISTORIAL ===
    stage_history_ids = fields.One2many(
        'hr.applicant.stage.history', 
        'applicant_id', 
        string='Historial de Etapas',
        help='Historial completo de etapas por las que ha pasado el candidato'
    )

    # Prueba de manejo
    is_driving_test = fields.Boolean(
        compute='_compute_is_driving_test',
        store=False
    )

    is_driving_test_editable = fields.Boolean(
        string='Es Editable Prueba de Manejo',
        compute='_compute_is_driving_test_editable',
        store=False
    )

    evaluator_id = fields.Many2one(
        'res.users',
        string='Evaluador Asignado',
        default=lambda self: self.env.user,
    )

    evaluator_job_title = fields.Char(
        string='Puesto del Evaluador',
        compute='_compute_evaluator_job_title',
        store=True,
        readonly=True
    )

    license_type = fields.Selection([
        ('tipo_a', 'Tipo A'),
        ('tipo_b', 'Tipo B'),
        ('tipo_c', 'Tipo C'),
        ('tipo_d', 'Tipo D'),
        ('tipo_e', 'Tipo E'),
        ('tipo_e_federal', 'Tipo E (Federal)'),
        ('permiso_provisional', 'Permiso Provisional'),
    ], string='Tipo de Licencia')

    license_description = fields.Text(
        string='Descripción de la Licencia',
        compute='_compute_license_description',
        store=False,
        readonly=True
    )

    license_number = fields.Char(string='Número de Licencia')

    # === EVALUACIÓN PRUEBA DE MANEJO ===
    # 1. CONOCIMIENTO, INSPECCIÓN Y ADAPTACIÓN DEL VEHÍCULO (5 factores)
    fluid_levels_inspection = fields.Selection([
        ('1', '1 - Deficiente'),
        ('2', '2 - Malo'),
        ('3', '3 - Regular'),
        ('4', '4 - Bueno'),
        ('5', '5 - Excelente')
    ], string='Inspección de los niveles (refrigerante, líquido de frenos, aceite)')

    battery_inspection = fields.Selection([
        ('1', '1 - Deficiente'),
        ('2', '2 - Malo'),
        ('3', '3 - Regular'),
        ('4', '4 - Bueno'),
        ('5', '5 - Excelente')
    ], string='Inspección de estado físico de la batería')

    tire_verification = fields.Selection([
        ('1', '1 - Deficiente'),
        ('2', '2 - Malo'),
        ('3', '3 - Regular'),
        ('4', '4 - Bueno'),
        ('5', '5 - Excelente')
    ], string='Verificación estado de llantas (Estado y presión)')

    safety_adaptation = fields.Selection([
        ('1', '1 - Deficiente'),
        ('2', '2 - Malo'),
        ('3', '3 - Regular'),
        ('4', '4 - Bueno'),
        ('5', '5 - Excelente')
    ], string='Adaptación o graduación del cinturón de seguridad, espejos laterales, asiento y retrovisor')

    lights_verification = fields.Selection([
        ('1', '1 - Deficiente'),
        ('2', '2 - Malo'),
        ('3', '3 - Regular'),
        ('4', '4 - Bueno'),
        ('5', '5 - Excelente')
    ], string='Verificación del estado de las luces (altas, bajas, direccionales, freno de parqueo)')

    # Promedio del Aspecto 1
    knowledge_average = fields.Float(
        string='Promedio Conocimiento e Inspección',
        compute='_compute_knowledge_average',
        store=True,
        digits=(3, 2)
    )

    # 2. DESTREZA Y HABILIDADES EN EL MANEJO (10 factores)
    ignition_maneuver = fields.Selection([
        ('1', '1 - Deficiente'),
        ('2', '2 - Malo'),
        ('3', '3 - Regular'),
        ('4', '4 - Bueno'),
        ('5', '5 - Excelente')
    ], string='Maniobra de encendido y arranque del vehículo')

    starting_movement = fields.Selection([
        ('1', '1 - Deficiente'),
        ('2', '2 - Malo'),
        ('3', '3 - Regular'),
        ('4', '4 - Bueno'),
        ('5', '5 - Excelente')
    ], string='Puesta en marcha en plano y en pendiente')

    straight_line_advance = fields.Selection([
        ('1', '1 - Deficiente'),
        ('2', '2 - Malo'),
        ('3', '3 - Regular'),
        ('4', '4 - Bueno'),
        ('5', '5 - Excelente')
    ], string='Avance en línea recta y con ángulos')

    maneuver_coordination = fields.Selection([
        ('1', '1 - Deficiente'),
        ('2', '2 - Malo'),
        ('3', '3 - Regular'),
        ('4', '4 - Bueno'),
        ('5', '5 - Excelente')
    ], string='Coordinación de maniobras: aceleración, freno, cambio y embrague')

    gear_application = fields.Selection([
        ('1', '1 - Deficiente'),
        ('2', '2 - Malo'),
        ('3', '3 - Regular'),
        ('4', '4 - Bueno'),
        ('5', '5 - Excelente')
    ], string='Aplicación de cambios ascendentes y descendentes')

    inclined_terrain = fields.Selection([
        ('1', '1 - Deficiente'),
        ('2', '2 - Malo'),
        ('3', '3 - Regular'),
        ('4', '4 - Bueno'),
        ('5', '5 - Excelente')
    ], string='Descenso y ascenso en terreno inclinado')

    circulation_overtaking = fields.Selection([
        ('1', '1 - Deficiente'),
        ('2', '2 - Malo'),
        ('3', '3 - Regular'),
        ('4', '4 - Bueno'),
        ('5', '5 - Excelente')
    ], string='Maniobra de circulación y adelantamiento')

    clutch_application = fields.Selection([
        ('1', '1 - Deficiente'),
        ('2', '2 - Malo'),
        ('3', '3 - Regular'),
        ('4', '4 - Bueno'),
        ('5', '5 - Excelente')
    ], string='Aplicación del embrague')

    brake_parking = fields.Selection([
        ('1', '1 - Deficiente'),
        ('2', '2 - Malo'),
        ('3', '3 - Regular'),
        ('4', '4 - Bueno'),
        ('5', '5 - Excelente')
    ], string='Aplicación de frenos y parqueo en reversa')

    parking_entry = fields.Selection([
        ('1', '1 - Deficiente'),
        ('2', '2 - Malo'),
        ('3', '3 - Regular'),
        ('4', '4 - Bueno'),
        ('5', '5 - Excelente')
    ], string='Ingreso al área de parqueo en reversa')

    # Promedio del Aspecto 2
    skills_average = fields.Float(
        string='Promedio Destreza y Habilidades',
        compute='_compute_skills_average',
        store=True,
        digits=(3, 2)
    )

    # 3. COMPORTAMIENTO DEL CONDUCTOR FRENTE AL TRÁNSITO (5 factores)
    regulation_employment = fields.Selection([
        ('1', '1 - Deficiente'),
        ('2', '2 - Malo'),
        ('3', '3 - Regular'),
        ('4', '4 - Bueno'),
        ('5', '5 - Excelente')
    ], string='Empleo del reglamento de tránsito (señalizaciones y límites de velocidad)')

    following_distance = fields.Selection([
        ('1', '1 - Deficiente'),
        ('2', '2 - Malo'),
        ('3', '3 - Regular'),
        ('4', '4 - Bueno'),
        ('5', '5 - Excelente')
    ], string='Distancia de seguimiento de parada y lateral')

    lane_changes = fields.Selection([
        ('1', '1 - Deficiente'),
        ('2', '2 - Malo'),
        ('3', '3 - Regular'),
        ('4', '4 - Bueno'),
        ('5', '5 - Excelente')
    ], string='Cambios de carril, de calzada y adelantamientos')

    lane_use = fields.Selection([
        ('1', '1 - Deficiente'),
        ('2', '2 - Malo'),
        ('3', '3 - Regular'),
        ('4', '4 - Bueno'),
        ('5', '5 - Excelente')
    ], string='Uso adecuado de cambio de carriles')

    directional_handling = fields.Selection([
        ('1', '1 - Deficiente'),
        ('2', '2 - Malo'),
        ('3', '3 - Regular'),
        ('4', '4 - Bueno'),
        ('5', '5 - Excelente')
    ], string='Manejo adecuado de las luces direccionales')

    # Promedio del Aspecto 3
    behavior_average = fields.Float(
        string='Promedio Comportamiento en Tránsito',
        compute='_compute_behavior_average',
        store=True,
        digits=(3, 2)
    )

    # PROMEDIO FINAL
    final_test_average = fields.Float(
        string='Calificación Final de la Prueba',
        compute='_compute_final_test_average',
        store=True,
        digits=(3, 2)
    )

    final_test_result = fields.Selection([
        ('not_evaluated', 'No Evaluado'),
        ('failed', 'Reprobado'),
        ('passed', 'Aprobado')
    ], string='Resultado Final', compute='_compute_final_test_result', store=True)

    @api.depends('fluid_levels_inspection', 'battery_inspection', 'tire_verification', 'safety_adaptation', 'lights_verification')
    def _compute_knowledge_average(self):
        for record in self:
            factors = [
                record.fluid_levels_inspection,
                record.battery_inspection,
                record.tire_verification,
                record.safety_adaptation,
                record.lights_verification
            ]
            
            # Filtrar solo los que tienen valor
            numeric_values = [int(factor) for factor in factors if factor]
            
            if numeric_values:
                record.knowledge_average = sum(numeric_values) / len(numeric_values)
            else:
                record.knowledge_average = 0.0

    @api.depends('ignition_maneuver', 'starting_movement', 'straight_line_advance', 'maneuver_coordination', 
                'gear_application', 'inclined_terrain', 'circulation_overtaking', 
                'clutch_application', 'brake_parking', 'parking_entry')
    def _compute_skills_average(self):
        for record in self:
            factors = [
                record.ignition_maneuver,
                record.starting_movement,
                record.straight_line_advance,
                record.maneuver_coordination,
                record.gear_application,
                record.inclined_terrain,
                record.circulation_overtaking,
                record.clutch_application,
                record.brake_parking,
                record.parking_entry
            ]
            
            # Filtrar solo los que tienen valor
            numeric_values = [int(factor) for factor in factors if factor]
            
            if numeric_values:
                record.skills_average = sum(numeric_values) / len(numeric_values)
            else:
                record.skills_average = 0.0

    @api.depends('regulation_employment', 'following_distance', 'lane_changes', 'lane_use', 'directional_handling')
    def _compute_behavior_average(self):
        for record in self:
            factors = [
                record.regulation_employment,
                record.following_distance,
                record.lane_changes,
                record.lane_use,
                record.directional_handling
            ]
            
            # Filtrar solo los que tienen valor
            numeric_values = [int(factor) for factor in factors if factor]
            
            if numeric_values:
                record.behavior_average = sum(numeric_values) / len(numeric_values)
            else:
                record.behavior_average = 0.0

    @api.depends('knowledge_average', 'skills_average', 'behavior_average')
    def _compute_final_test_average(self):
        for record in self:
            averages = [
                record.knowledge_average,
                record.skills_average,
                record.behavior_average
            ]
            
            # Filtrar solo los que tienen valor mayor a 0
            valid_averages = [avg for avg in averages if avg > 0]
            
            if valid_averages:
                record.final_test_average = sum(valid_averages) / len(valid_averages)
            else:
                record.final_test_average = 0.0

    @api.depends('final_test_average')
    def _compute_final_test_result(self):
        for record in self:
            if record.final_test_average == 0:
                record.final_test_result = 'not_evaluated'
            elif record.final_test_average >= 3.0:  # 3.0 o más para aprobar
                record.final_test_result = 'passed'
            else:
                record.final_test_result = 'failed'

    @api.depends('evaluator_id')
    def _compute_evaluator_job_title(self):
        for record in self:
            if record.evaluator_id:
                # ✅ OPCIÓN 1: Buscar empleado asociado al usuario
                if record.evaluator_id.employee_id:
                    employee = record.evaluator_id.employee_id
                    record.evaluator_job_title = (
                        employee.job_title or 
                        employee.job_id.name or 
                        'Empleado sin puesto definido'
                    )
                
                # ✅ OPCIÓN 2: Si no hay empleado, buscar por user_id
                else:
                    employee = self.env['hr.employee'].search([
                        ('user_id', '=', record.evaluator_id.id)
                    ], limit=1)
                    
                    if employee:
                        record.evaluator_job_title = (
                            employee.job_title or 
                            employee.job_id.name or 
                            'Empleado sin puesto definido'
                        )
                    else:
                        # ✅ FALLBACK: Usar información del usuario
                        record.evaluator_job_title = f"Usuario: {record.evaluator_id.name}"
            else:
                record.evaluator_job_title = 'No asignado'

    @api.depends('license_type')
    def _compute_license_description(self):
        """Mostrar descripción detallada según el tipo de licencia seleccionado"""
        license_descriptions = {
            'tipo_a': 'Para conducir vehículos particulares, como automóviles.',
            'tipo_b': 'Para transporte público (aunque no se considera de servicio particular).',
            'tipo_c': 'Para conducir motocicletas.',
            'tipo_d': 'Para transporte masivo y autobuses (aunque no es de servicio particular).',
            'tipo_e': 'Para conducir vehículos particulares y de carga de hasta 3.5 toneladas, así como para choferes de servicio particular.',
            'tipo_e_federal': 'Para transporte de materiales y residuos peligrosos (aunque no es de uso particular).',
            'permiso_provisional': 'Para menores de edad (16 a 18 años) que deseen conducir vehículos particulares.',
        }
        
        for record in self:
            record.license_description = license_descriptions.get(record.license_type, '')

    @api.depends('stage_id.sequence')
    def _compute_is_driving_test_editable(self):
        for record in self:
            if record.stage_id:
                # ✅ Buscar la etapa "Prueba de Manejo" para obtener su sequence exacto
                driving_test_stage = self.env['hr.recruitment.stage'].search([
                    ('name', 'ilike', 'prueba de manejo')
                ], limit=1)
                
                if driving_test_stage:
                    # ✅ Solo editable cuando está EXACTAMENTE en "Prueba de Manejo"
                    record.is_driving_test_editable = record.stage_id.sequence == driving_test_stage.sequence
                else:
                    record.is_driving_test_editable = False
            else:
                record.is_driving_test_editable = False

    def action_save_driving_test(self):
        """Guardar la información de prueba de manejo"""
        # ✅ Verificación adicional de seguridad
        if not self.is_driving_test_editable:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Acción no permitida',
                    'message': 'No puede editar la prueba de manejo en esta etapa.',
                    'type': 'warning',
                }
            }
        
        # ✅ Validaciones básicas
        if not self.license_type:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Datos Incompletos',
                    'message': 'Debe seleccionar un tipo de licencia.',
                    'type': 'warning',
                }
            }
        
        # ✅ Asegurar que el evaluador esté asignado
        if not self.evaluator_id:
            self.evaluator_id = self.env.user.id
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Información Guardada',
                'message': f'La información de licencia para {self.partner_name} ha sido guardada exitosamente.',
                'type': 'success',
            }
        }

    @api.onchange('zoonosis')
    def _onchange_zoonosis(self):
        if self.zoonosis != 'positive':
            self.pet = False

    @api.onchange('tattoos_piercings')
    def _onchange_tattoos_piercings(self):
        if self.tattoos_piercings != 'positive':
            self.tattoos_number = False

    @api.depends('create_date', 'date_closed')
    def _compute_process_duration(self):
        for rec in self:
            if rec.create_date:
                end_date = rec.date_closed or fields.Datetime.now()
                duration = end_date - rec.create_date
                days = duration.days
                hours = duration.seconds // 3600
                minutes = (duration.seconds % 3600) // 60
                rec.process_duration = f"{days}d {hours}h {minutes}m"
            else:
                rec.process_duration = ''

    @api.depends('job_id')
    def _compute_user(self):
        """Override to prevent automatic assignment of user_id based on job_id."""
        for applicant in self:
            if not applicant.user_id:  # Solo asignar si no hay un reclutador definido
                applicant.user_id = self.env.user

    @api.model
    def create(self, vals):
        if 'user_id' not in vals or not vals['user_id']:
            vals['user_id'] = self.env.user.id  # Asigna el usuario logueado por defecto
        
        # Crear el applicant
        applicant = super(HrApplicant, self).create(vals)
        
        # === NUEVO: Crear historial inicial ===
        if applicant.stage_id:
            self.env['hr.applicant.stage.history'].create({
                'applicant_id': applicant.id,
                'stage_id': applicant.stage_id.id,
                'enter_date': fields.Datetime.now(),
            })
        
        return applicant
    
    def write(self, vals):
        # Validar si el postulante está bloqueado
        if 'stage_id' in vals and any(applicant.kanban_state == 'blocked' for applicant in self):
            raise UserError(_("El postulante está bloqueado y no puede avanzar en el proceso hasta que el bloqueo sea resuelto o eliminado manualmente por un usuario autorizado."))

        # === NUEVO: Manejar cambios de etapa para historial ===
        if 'stage_id' in vals and vals['stage_id']:
            for applicant in self:
                old_stage_id = applicant.stage_id.id if applicant.stage_id else False
                new_stage_id = vals['stage_id']
                
                # Solo procesar si realmente cambió la etapa
                if old_stage_id != new_stage_id:
                    now = fields.Datetime.now()
                    
                    # 1. Si no tiene historial previo, crear registro para la etapa actual (antes del cambio)
                    if not applicant.stage_history_ids and old_stage_id:
                        self.env['hr.applicant.stage.history'].create({
                            'applicant_id': applicant.id,
                            'stage_id': old_stage_id,
                            'enter_date': applicant.date_last_stage_update or applicant.create_date,
                            'leave_date': now,
                        })
                    
                    # 2. Cerrar la etapa anterior (si existe y tiene historial)
                    elif old_stage_id:
                        current_history = applicant.stage_history_ids.filtered(
                            lambda h: h.stage_id.id == old_stage_id and not h.leave_date
                        )
                        if current_history:
                            current_history.write({'leave_date': now})
                    
                    # 3. Crear nueva entrada de historial
                    self.env['hr.applicant.stage.history'].create({
                        'applicant_id': applicant.id,
                        'stage_id': new_stage_id,
                        'enter_date': now,
                    })

        # Preservar el reclutador (user_id) si no está en los valores
        if 'user_id' not in vals:
            for record in self:
                if record.user_id:
                    vals['user_id'] = record.user_id.id

        return super(HrApplicant, self).write(vals)
    
    # Computed fields
    @api.depends('weight', 'height')
    def _compute_bmi(self):
        for record in self:
            if record.weight and record.height:
                height_in_meters = record.height / 100
                record.bmi = round(record.weight / (height_in_meters ** 2), 1)
            else:
                record.bmi = 0

    @api.depends()
    def _compute_treatment_recommendations(self):
        for record in self:
            record.treatment_recommendations = _(
                "Dieta rica en verduras, baja en carbohidratos, tomar abundante líquido, moderar el consumo de carnes rojas, embutidos y lácteos. "
                "Evitar cambios bruscos de temperatura, realizar actividad física diariamente (caminata ligera a tolerancia), se promueve la salud bucal, "
                "hábitos higiénicos generales, evitar accidentes. Se consulta guía de práctica clínica, se realizan acciones del servicio de promoción y "
                "prevención para una mejor salud."
            )

    @api.depends('birth_date')
    def _compute_age(self):
        for record in self:
            if record.birth_date:
                today = date.today()
                age = today.year - record.birth_date.year - ((today.month, today.day) < (record.birth_date.month, record.birth_date.day))
                record.age = f"{age} años"
            else:
                record.age = "0 años"

    def _compute_work_center(self):
        for record in self:
            record.work_center = record.company_id.name

    def _compute_patient_name(self):
        for record in self:
            record.patient_name = record.partner_name

    def _compute_job_position(self):
        for record in self:
            record.job_position = record.job_id.name

    def _compute_phone(self):
        for record in self:
            record.phone = record.partner_phone

    def _compute_professional_license(self):
        for record in self:
            record.professional_license = "1234567890"  # Replace with actual logic

    def _compute_applicant_documents(self):
        for record in self:
            record.documents_count = self.env['ir.attachment'].search_count(
                [('res_model', '=', 'hr.applicant'), ('res_id', '=', record.id)])
    
    def action_open_documents(self):
        self.env['hr.applicant.document'].search([]).unlink()
        docs = self.env['hr.applicant.document'].create_required_documents(self.id)

        return {
            'name': _('Documentos del Aplicante'),
            'view_mode': 'kanban',
            'res_model': 'hr.applicant.document',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {'create': False},
            'views': [(self.env.ref('hr_recruitment_estevez.view_hr_applicant_documents_kanban').id, 'kanban')],  # Asegúrate de usar la vista correcta
        }

    def _format_phone_number(self, phone_number):
        if phone_number and not phone_number.startswith('+52'):
            phone_number = '+52 ' + re.sub(r'(\d{3})(\d{3})(\d{4})', r'\1 \2 \3', phone_number)
        return phone_number

    @api.onchange('partner_phone')
    def _onchange_partner_phone(self):
        if self.partner_phone:
            self.partner_phone = self._format_phone_number(self.partner_phone)

    @api.onchange('candidate_id')
    def _onchange_candidate_id_fill_info(self):
        if self.candidate_id:            
            self.phone = self.candidate_id.partner_phone            
            self.source_id = self.candidate_id.source_id.id            
            self.job_id = self.candidate_id.job_ids.id           


    def action_open_whatsapp(self):
        for applicant in self:
            if applicant.partner_phone:
                # Eliminar caracteres no numéricos
                phone = re.sub(r'\D', '', applicant.partner_phone)
                # Verificar si el número ya tiene un código de país
                if not phone.startswith('52'):
                    phone = '52' + phone
                message = "Hola! Queremos comunicarnos contigo!"
                url = f"https://wa.me/{phone}?text={message}"
                _logger.info(f"Opening WhatsApp with phone number: {phone}")
                return {
                    'type': 'ir.actions.act_url',
                    'url': url,
                    'target': 'new',
                }
            else:
                raise UserError("The applicant does not have a phone number.")
            

    def check_stage_time_to_bocked(self, stage_name, time_delta):
        # Buscar el stage por nombre, sin sensibilidad a mayúsculas/minúsculas
        stage = self.env['hr.recruitment.stage'].search([('name', 'ilike', stage_name)], limit=1)
        if not stage:
            _logger.error(f"Stage '{stage_name}' not found")
            return

        # Calcular el tiempo límite
        time_limit = fields.Datetime.now() - timedelta(hours=time_delta)

        applicants = self.search([
            ('stage_id', '=', stage.id),
            ('kanban_state', '!=', 'blocked'),
            ('date_last_stage_update', '<=', time_limit)
        ])

        _logger.info(f"Found {len(applicants)} applicants to block in stage {stage_name}")

        for applicant in applicants:
            # Verificar si el aplicante tiene actividades programadas para una fecha y hora posterior a la fecha y hora actual
            future_activities = self.env['mail.activity'].search([
                ('res_model', '=', 'hr.applicant'),
                ('res_id', '=', applicant.id),
                ('date_deadline', '>', fields.Datetime.now())
            ])
            
            if future_activities:
                _logger.info(f"Applicant {applicant.id} has future activities and will not be blocked")
                continue

            applicant.write({
                'kanban_state': 'blocked'
            })
            # Notificar al reclutador
            applicant.message_post(
                body=f"¡Ups! El candidato {applicant.partner_name} sigue en espera. Quizás sea un buen momento para revisar su estatus. 😉",
                subtype_id=self.env.ref('mail.mt_comment').id
            )
            _logger.info(f"Applicant {applicant.id} blocked and notified")

    @api.depends('stage_id.name')
    def _compute_is_examen_medico(self):
        for record in self:
            stage_name = record.stage_id.name
            if stage_name:
                record.is_examen_medico = stage_name == 'Examen Médico'
            else:
                record.is_examen_medico = False

    @api.depends('stage_id.sequence')
    def _compute_is_driving_test(self):
        for record in self:
            if record.stage_id:
                # ✅ Buscar la etapa "Prueba de Manejo" para obtener su sequence
                driving_test_stage = self.env['hr.recruitment.stage'].search([
                    ('name', 'ilike', 'prueba de manejo')
                ], limit=1)
                
                if driving_test_stage:
                    # ✅ Visible si está en "Prueba de Manejo" o en etapas posteriores (sequence mayor o igual)
                    record.is_driving_test = record.stage_id.sequence >= driving_test_stage.sequence
                else:
                    record.is_driving_test = False
            else:
                record.is_driving_test = False

    def create_employee_from_applicant(self):
        self.ensure_one()
        
        # Llamar al método original para crear el empleado
        action = self.candidate_id.create_employee_from_candidate()
        employee = self.env['hr.employee'].browse(action['res_id'])
        
        # Actualizar los datos del empleado con información del applicant
        employee.write({
            'job_id': self.job_id.id,
            'job_title': self.job_id.name,
            'department_id': self.department_id.id,
            'work_email': self.department_id.company_id.email or self.email_from,  # Para tener un correo válido por defecto
            'work_phone': self.department_id.company_id.phone,
        })

        # Transferir documentos asociados al applicant al empleado
        attachments = self.env['ir.attachment'].search([
            ('res_model', '=', 'hr.applicant'),
            ('res_id', '=', self.id)
        ])
        for attachment in attachments:
            attachment.copy({
                'res_model': 'hr.employee',
                'res_id': employee.id,
            })

        return action