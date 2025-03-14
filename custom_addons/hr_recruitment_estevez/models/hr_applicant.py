from odoo import models, api, fields, _
from odoo.exceptions import UserError
from datetime import timedelta, date
import base64
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
    construction_material = fields.Selection([('durable', 'Durable'), ('non_durable', 'No Durable')], string="Material de Construcción")
    housing_services = fields.Char(string="Servicios de Vivienda")
    weekly_clothing_change = fields.Char(string="Cambio de Ropa Semanal")
    occupations = fields.Text(string="Oficios Desempeñados")
    daily_teeth_brushing = fields.Integer(string="Cepillado de Dientes Diario")
    zoonosis = fields.Selection([('negative', 'Negativo'), ('positive', 'Positivo')], string="Zoonosis")
    overcrowding = fields.Selection([('negative', 'Negativo'), ('positive', 'Positivo')], string="Hacinamiento")
    tattoos_piercings = fields.Char(string="Tatuajes y Perforaciones")
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
    treatment_recommendations = fields.Text(string="Tratamiento e Indicaciones")

    # Próxima Cita
    next_appointment = fields.Text(string="Próxima Cita")

    # Pronóstico
    prognosis = fields.Text(string="Pronóstico")

    # Firmas
    doctor_signature = fields.Binary(string="Firma del Doctor")
    professional_license = fields.Char(string="Cédula Profesional", compute="_compute_professional_license")
    worker_signature = fields.Binary(string="Firma del Trabajador")

    documents_count = fields.Integer(
        'Documents Count', compute="_compute_applicant_documents")
    
    # Computed fields
    @api.depends('weight', 'height')
    def _compute_bmi(self):
        for record in self:
            if record.weight and record.height:
                height_in_meters = record.height / 100
                record.bmi = record.weight / (height_in_meters ** 2)
            else:
                record.bmi = 0

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

    def action_open_whatsapp(self):
        for applicant in self:
            if applicant.partner_phone:
                # Eliminar caracteres no numéricos
                phone = re.sub(r'\D', '', applicant.partner_phone)
                # Verificar si el número ya tiene un código de país
                if not phone.startswith('52'):
                    phone = '52' + phone
                message = "Hola"
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

    def write(self, vals):
        if 'stage_id' in vals and any(applicant.kanban_state == 'blocked' for applicant in self):
            raise UserError(_("El postulante está bloqueado y no puede avanzar en el proceso hasta que el bloqueo sea resuelto o eliminado manualmente por un usuario autorizado."))
        return super(HrApplicant, self).write(vals)

    @api.depends('stage_id.name')
    def _compute_is_examen_medico(self):
        for record in self:
            stage_name = record.stage_id.name
            if stage_name:
                record.is_examen_medico = stage_name == 'Examen Médico'
            else:
                record.is_examen_medico = False