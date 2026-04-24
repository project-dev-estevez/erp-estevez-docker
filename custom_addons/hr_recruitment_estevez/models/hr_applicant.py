from odoo import models, api, fields, _
from odoo.exceptions import UserError
from datetime import timedelta, date
import werkzeug
import logging
import re
from ..tools import strip_accents_keep_enye

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
    # En tu modelo hr.applicant
    employee_id = fields.Many2one('hr.employee', string='Empleado Relacionado')

    # Antecedentes Heredo Familiares
    family_medical_history = fields.Text(string="Antecedentes Heredo Familiares")

    # Antecedentes Personales No Patológicos
    place_of_origin = fields.Char(string="Lugar de Origen")
    place_of_residence = fields.Char(string="Lugar de Residencia")
    marital_status = fields.Selection([
        ('single', 'Soltero(a)'),
        ('married', 'Casado(a)'),
        ('cohabitant', 'Unión Libre'),
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

    first_name = fields.Char(string="Nombre(s)", required=True)    
    last_name = fields.Char(string="Apellido Paterno", required=True)
    mother_last_name = fields.Char(string="Apellido Materno", required=True)

        

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

        # Normalizar nombres: quitar tildes preservando ñ/Ñ
        for field in ('first_name', 'last_name', 'mother_last_name'):
            if vals.get(field):
                vals[field] = strip_accents_keep_enye(vals[field])

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
        # Normalizar nombres: quitar tildes preservando ñ/Ñ
        for field in ('first_name', 'last_name', 'mother_last_name'):
            if vals.get(field):
                vals[field] = strip_accents_keep_enye(vals[field])

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
        result = super(HrApplicant, self).write(vals)                
    
        for applicant in self:
            if applicant.employee_id:
                try:
                    applicant.sync_attachment_changes(applicant.employee_id.id)
                    _logger.info(f"Attachments sincronizados automáticamente para applicant {applicant.id}")
                except Exception as e:
                    _logger.error(f"Error sincronizando attachments para applicant {applicant.id}: {e}")
        
        return result
    
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
        self.ensure_one()
        self.env['hr.applicant.document'].search([('applicant_id', '=', self.id)]).unlink()
        self.env['hr.applicant.document'].create_required_documents(self.id)
        return {
            'name': _('Documentos del Aplicante'),
            'view_mode': 'kanban',
            'res_model': 'hr.applicant.document',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {'create': False},
            'domain': [('applicant_id', '=', self.id)],
            'views': [(self.env.ref('hr_recruitment_estevez.view_hr_applicant_documents_kanban').id, 'kanban')],
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
            self.job_id = self.candidate_id.job_id.id           


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

        if not self.candidate_id:
            raise UserError(_("No hay candidato asociado para crear el empleado."))
        
        candidate = self.candidate_id

        # Datos del candidato
        first_name = candidate.first_name or self.first_name or ''
        last_name = candidate.last_name or self.last_name or ''
        mother_last_name = candidate.mother_last_name or self.mother_last_name or ''

        # Validar si falta apellido paterno
        if not last_name:
            raise UserError(_("El apellido paterno es obligatorio para crear el empleado."))

        # Construir nombre completo
        full_name = f"{first_name} {last_name} {mother_last_name}".strip()

        job = self.job_id
        direction_id = job.direction_id.id if job and job.direction_id else False
        department_id = job.department_id.id if job and job.department_id else self.department_id.id
        area_id = job.area_id.id if job and job.area_id else False

        employee_vals = {
            'name': full_name,
            'names': first_name,
            'last_name': last_name,
            'mother_last_name': mother_last_name,
            'job_id': self.job_id.id,
            'job_title': self.job_id.name,
            'direction_id': direction_id,
            'department_id': department_id,
            'area_id': area_id,
            'private_email': self.email_from or candidate.email or (self.department_id.company_id.email if self.department_id and self.department_id.company_id else False),
            'work_phone': self.department_id.company_id.phone or self.partner_phone or candidate.phone,
            'project': self.project_id.name,
        }

        # Crear empleado directamente
        employee = self.env['hr.employee'].with_context(from_recruitment=True).create(employee_vals)
        self.employee_id = employee.id

        # Transferir categorías
        for appl_cat in self.categ_ids:
            emp_cat = self.env['hr.employee.category'].search(
                [('name', '=ilike', appl_cat.name.strip())], limit=1
            )
            if not emp_cat:
                emp_cat = self.env['hr.employee.category'].create({'name': appl_cat.name.strip()})
            if emp_cat.id not in employee.category_ids.ids:
                employee.write({'category_ids': [(4, emp_cat.id)]})

        # Sincronizar attachments (NUEVA IMPLEMENTACIÓN)
        self._sync_attachments_to_employee(employee)

        # Log
        _logger.info(
            "Empleado creado manualmente: names=%s last_name=%s mother_last_name=%s",
            employee.names, employee.last_name, employee.mother_last_name
        )

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'hr.employee',
            'view_mode': 'form',
            'res_id': employee.id,
        }

    def _sync_attachments_to_employee(self, employee):
        """Sincroniza attachments del applicant al employee"""
        attachments = self.env['ir.attachment'].search([
            ('res_model', '=', 'hr.applicant'),
            ('res_id', '=', self.id)
        ])
        
        for attachment in attachments:
            # Buscar si ya existe el mismo archivo en el empleado
            existing_attachment = self.env['ir.attachment'].search([
                ('res_model', '=', 'hr.employee'),
                ('res_id', '=', employee.id),
                ('name', '=', attachment.name),
            ], limit=1)
            
            if not existing_attachment:
                # Crear nueva copia
                attachment.copy({
                    'res_model': 'hr.employee',
                    'res_id': employee.id,
                })

    def sync_attachment_changes(self, employee_id, direction='applicant_to_employee'):
        """Sincroniza cambios de attachments - ahora bidireccional"""
        employee = self.env['hr.employee'].browse(employee_id)
        
        if direction == 'applicant_to_employee':
            
            applicant_attachments = self.env['ir.attachment'].search([
                ('res_model', '=', 'hr.applicant'),
                ('res_id', '=', self.id)
            ])
            
            applicant_files = {att.name: att for att in applicant_attachments}
            
            employee_attachments = self.env['ir.attachment'].search([
                ('res_model', '=', 'hr.employee'),
                ('res_id', '=', employee.id)
            ])
            
            # Sincronizar: actualizar archivos existentes
            for emp_att in employee_attachments:
                if emp_att.name in applicant_files:
                    app_att = applicant_files[emp_att.name]
                    if app_att.datas != emp_att.datas:
                        emp_att.write({'datas': app_att.datas})
            
            # Agregar nuevos archivos
            for app_name, app_att in applicant_files.items():
                if app_name not in [e.name for e in employee_attachments]:
                    app_att.copy({
                        'res_model': 'hr.employee',
                        'res_id': employee.id,
                    })
            
            # Eliminar archivos del empleado que ya no existen en el applicant
            #for emp_att in employee_attachments:
            #    if emp_att.name not in applicant_files:
            #        emp_att.unlink()
                    
        elif direction == 'employee_to_applicant':
            
            employee_attachments = self.env['ir.attachment'].search([
                ('res_model', '=', 'hr.employee'),
                ('res_id', '=', employee.id)
            ])
            
            employee_files = {att.name: att for att in employee_attachments}
            
            applicant_attachments = self.env['ir.attachment'].search([
                ('res_model', '=', 'hr.applicant'),
                ('res_id', '=', self.id)
            ])
            
            # Sincronizar: actualizar archivos existentes
            for app_att in applicant_attachments:
                if app_att.name in employee_files:
                    emp_att = employee_files[app_att.name]
                    if emp_att.datas != app_att.datas:
                        app_att.write({'datas': emp_att.datas})
            
            # Agregar nuevos archivos
            for emp_name, emp_att in employee_files.items():
                if emp_name not in [a.name for a in applicant_attachments]:
                    emp_att.copy({
                        'res_model': 'hr.applicant',
                        'res_id': self.id,
                    })
            
            # Eliminar archivos del applicant que ya no existen en el employee
            #for app_att in applicant_attachments:
             #   if app_att.name not in employee_files:
              #      app_att.unlink()

    def action_sync_attachments(self):
        """Acción para sincronizar attachments manualmente"""
        for applicant in self:
            # Buscar el empleado relacionado
            if hasattr(applicant, 'employee_id') and applicant.employee_id:
                applicant.sync_attachment_changes(applicant.employee_id.id, 'applicant_to_employee')
            else:
                # Si no hay campo employee_id, buscar por nombre/email
                employee = self.env['hr.employee'].search([
                    '|',
                    ('name', '=ilike', applicant.partner_name),
                    ('work_email', '=ilike', applicant.email_from)
                ], limit=1)
                if employee:
                    applicant.sync_attachment_changes(employee.id, 'applicant_to_employee')
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Sincronización completada',
                'message': 'Los documentos se han sincronizado correctamente',
                'type': 'success',
                'sticky': False,
            }
        }

    def action_save(self):
        self.ensure_one()

        _logger.info("Mostrando vista lista + efecto rainbow_man")

        return {
            'effect': { 
                'fadeout': 'slow',
                'message': '¡Postulación registrada exitosamente!',
                'type': 'rainbow_man',
            },
            'type': 'ir.actions.act_window',
            'res_model': self._name, 
            'view_mode': 'list',
            'target': 'current',
            
        }

class IrAttachmentSync(models.Model):
    _inherit = 'ir.attachment'

    def write(self, vals):
        result = super(IrAttachmentSync, self).write(vals)
        
        for attachment in self:
            # ✅ De APPLICANT → EMPLOYEE
            if attachment.res_model == 'hr.applicant' and attachment.res_id:
                applicant = self.env['hr.applicant'].browse(attachment.res_id)
                if applicant.exists() and applicant.employee_id:
                    try:
                        applicant.sync_attachment_changes(applicant.employee_id.id, 'applicant_to_employee')
                        _logger.info(f"Sync APPLICANT→EMPLOYEE para applicant {applicant.id}")
                    except Exception as e:
                        _logger.error(f"Error sync APPLICANT→EMPLOYEE: {e}")
            
            # ✅ NUEVO: De EMPLOYEE → APPLICANT  
            elif attachment.res_model == 'hr.employee' and attachment.res_id:
                employee = self.env['hr.employee'].browse(attachment.res_id)
                if employee.exists():
                    # Buscar el applicant relacionado con este employee
                    applicant = self.env['hr.applicant'].search([
                        ('employee_id', '=', employee.id)
                    ], limit=1)
                    if applicant:
                        try:
                            applicant.sync_attachment_changes(employee.id, 'employee_to_applicant')
                            _logger.info(f"Sync EMPLOYEE→APPLICANT para employee {employee.id}")
                        except Exception as e:
                            _logger.error(f"Error sync EMPLOYEE→APPLICANT: {e}")
        
        return result

    @api.model_create_multi
    def create(self, vals_list):
        records = super(IrAttachmentSync, self).create(vals_list)
        
        for record in records:
            # ✅ De APPLICANT → EMPLOYEE
            if record.res_model == 'hr.applicant' and record.res_id:
                applicant = self.env['hr.applicant'].browse(record.res_id)
                if applicant.exists() and applicant.employee_id:
                    try:
                        applicant.sync_attachment_changes(applicant.employee_id.id, 'applicant_to_employee')
                        _logger.info(f"CREATE Sync APPLICANT→EMPLOYEE para applicant {applicant.id}")
                    except Exception as e:
                        _logger.error(f"Error CREATE sync APPLICANT→EMPLOYEE: {e}")
            
            # ✅ NUEVO: De EMPLOYEE → APPLICANT
            elif record.res_model == 'hr.employee' and record.res_id:
                employee = self.env['hr.employee'].browse(record.res_id)
                if employee.exists():
                    applicant = self.env['hr.applicant'].search([
                        ('employee_id', '=', employee.id)
                    ], limit=1)
                    if applicant:
                        try:
                            applicant.sync_attachment_changes(employee.id, 'employee_to_applicant')
                            _logger.info(f"CREATE Sync EMPLOYEE→APPLICANT para employee {employee.id}")
                        except Exception as e:
                            _logger.error(f"Error CREATE sync EMPLOYEE→APPLICANT: {e}")
        
        return records
    