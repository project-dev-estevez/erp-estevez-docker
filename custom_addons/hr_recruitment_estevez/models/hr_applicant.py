from odoo import models, api, fields, _
from odoo.exceptions import UserError
from datetime import timedelta
import json
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
    age = fields.Integer(string="Edad")
    job_position = fields.Char(string="Puesto de Trabajo", compute="_compute_job_position")
    education = fields.Char(string="Escolaridad")
    address = fields.Text(string="Dirección")
    phone = fields.Char(string="Teléfono", compute="_compute_phone")

    # Antecedentes Heredo Familiares
    family_medical_history = fields.Text(string="Antecedentes Heredo Familiares")

    # Antecedentes Personales No Patológicos
    place_of_origin = fields.Char(string="Lugar de Origen")
    place_of_residence = fields.Char(string="Lugar de Residencia")
    marital_status = fields.Selection([('single', 'Soltero'), ('married', 'Casado')], string="Estado Civil")
    religion = fields.Char(string="Religión")
    housing_type = fields.Selection([('own', 'Propia'), ('rented', 'Rentada')], string="Tipo de Vivienda")
    construction_material = fields.Selection([('durable', 'Durable'), ('non_durable', 'No Durable')], string="Material de Construcción")
    housing_services = fields.Char(string="Servicios de Vivienda")
    weekly_clothing_change = fields.Integer(string="Cambio de Ropa Semanal")
    daily_teeth_brushing = fields.Integer(string="Cepillado de Dientes Diario")
    zoonosis = fields.Selection([('negative', 'Negativo'), ('positive', 'Positivo')], string="Zoonosis")
    overcrowding = fields.Selection([('negative', 'Negativo'), ('positive', 'Positivo')], string="Hacinamiento")
    tattoos_piercings = fields.Char(string="Tatuajes y Perforaciones")
    blood_type = fields.Char(string="Tipo de Sangre")
    donor = fields.Boolean(string="Donador")

    # Antecedentes Personales Patológicos
    previous_surgeries = fields.Char(string="Quirúrgicos")
    traumas = fields.Char(string="Traumáticos")
    transfusions = fields.Char(string="Transfusionales")
    allergies = fields.Char(string="Alérgicos")
    chronic_diseases = fields.Char(string="Crónico-degenerativos")
    childhood_diseases = fields.Char(string="Enfermedades de la Infancia")
    smoking = fields.Selection([('yes', 'Sí'), ('no', 'No')], string="Tabaquismo")
    alcoholism = fields.Selection([('yes', 'Sí'), ('no', 'No')], string="Alcoholismo")
    drug_addiction = fields.Char(string="Toxicomanías")

    # Esquema de Vacunación
    complete_schedule = fields.Selection([('yes', 'Sí'), ('no', 'No')], string="Esquema Completo")
    no_vaccination_card = fields.Boolean(string="Sin Cartilla de Vacunación")
    last_vaccine = fields.Date(string="Última Vacuna")

    # Examen Físico
    heart_rate = fields.Integer(string="Cardiovascular (LPM)")
    respiratory_rate = fields.Integer(string="Respiratorio (RPM)")
    temperature = fields.Float(string="Gastrointestinal")
    blood_pressure = fields.Char(string="Genitourinario")
    oxygen_saturation = fields.Float(string="Endócrino")
    weight = fields.Float(string="Nervioso")
    height = fields.Float(string="Musculoesquelético")
    bmi = fields.Float(string="Piel, mucosas y anexos")

    # Diagnóstico y Tratamiento
    clinical_diagnosis = fields.Text(string="Diagnóstico Clínico")
    treatment_instructions = fields.Text(string="Tratamiento e Instrucciones")
    next_appointment = fields.Date(string="Próxima Cita")
    prognosis = fields.Char(string="Pronóstico")

    # Firmas
    doctor_signature = fields.Binary(string="Firma del Doctor")
    professional_license = fields.Char(string="Cédula Profesional", compute="_compute_professional_license")
    worker_signature = fields.Binary(string="Firma del Trabajador")

    documents_count = fields.Integer(
        'Documents Count', compute="_compute_applicant_documents")
    

    # Computed fields
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
            
    def action_save(self):
        # Save the record
        self.ensure_one()
        self.write(self._context.get('params', {}))
        # Generate the PDF report
        return self.env.ref('hr_recruitment_estevez.action_report_hr_applicant_document').report_action(self)


    @api.model
    def check_first_contact_stage(self):
        # Buscar el stage por nombre, sin sensibilidad a mayúsculas/minúsculas
        first_contact_stage = self.env['hr.recruitment.stage'].search([('name', 'ilike', 'primer contacto')], limit=1)
        if not first_contact_stage:
            _logger.error("Stage 'Primer Contacto' not found")
            return
        
        # Buscar o crear el tag "Falta de seguimiento"
        tag_name = "Falta de seguimiento"
        tag = self.env['hr.applicant.category'].search([('name', '=', tag_name)], limit=1)
        if not tag:
            tag = self.env['hr.applicant.category'].create({'name': tag_name})
        
        applicants = self.search([
            ('stage_id', '=', first_contact_stage.id),
            ('kanban_state', '!=', 'blocked'),
            ('date_last_stage_update', '<=', fields.Datetime.now() - timedelta(hours=24))
        ])
        for applicant in applicants:
            applicant.write({
                'kanban_state': 'blocked',
                'categ_ids': [(4, tag.id)]
            })
            # Notificar al reclutador
            applicant.message_post(
                body="El postulante ha sido bloqueado por falta de seguimiento.",
                subtype_id=self.env.ref('mail.mt_comment').id
            )

    @api.model
    def check_interview_stage(self):
        _logger.info("Executing check_interview_stage")
        
        # Buscar el stage por nombre, sin sensibilidad a mayúsculas/minúsculas
        interview_stage = self.env['hr.recruitment.stage'].search([('name', 'ilike', 'entrevista')], limit=1)
        if not interview_stage:
            _logger.error("Stage 'Entrevista' not found")
            return
        
        # Buscar o crear el tag "Reprogramar entrevista"
        tag_name = "Reprogramar entrevista"
        tag = self.env['hr.applicant.category'].search([('name', '=', tag_name)], limit=1)
        if not tag:
            tag = self.env['hr.applicant.category'].create({'name': tag_name})
        
        applicants = self.search([
            ('stage_id', '=', interview_stage.id),
            ('kanban_state', '!=', 'blocked'),
            ('date_last_stage_update', '<=', fields.Datetime.now() - timedelta(hours=24))
        ])
        _logger.info(f"Found {len(applicants)} applicants to block")
        for applicant in applicants:
            applicant.write({
                'kanban_state': 'blocked',
                'categ_ids': [(4, tag.id)]
            })
            # Notificar al reclutador
            applicant.message_post(
                body="El candidato ha sido bloqueado, se debe reprogramar entrevista.",
                subtype_id=self.env.ref('mail.mt_comment').id
            )

    @api.model
    def check_psychometric_tests_stage(self):
        
        # Buscar el stage por nombre, sin sensibilidad a mayúsculas/minúsculas
        psychometric_tests_stage = self.env['hr.recruitment.stage'].search([('name', 'ilike', 'pruebas psicométricas')], limit=1)
        
        # Buscar o crear el tag "No realizar pruebas"
        tag_name = "No realizó pruebas a tiempo"
        tag = self.env['hr.applicant.category'].search([('name', '=', tag_name)], limit=1)
        if not tag:
            tag = self.env['hr.applicant.category'].create({'name': tag_name})
        
        applicants = self.search([
            ('stage_id', '=', psychometric_tests_stage.id),
            ('kanban_state', '!=', 'blocked'),
            ('date_last_stage_update', '<=', fields.Datetime.now() - timedelta(hours=24))
        ])
        _logger.info(f"Found {len(applicants)} applicants to block")
        for applicant in applicants:
            applicant.write({
                'kanban_state': 'blocked',
                'categ_ids': [(4, tag.id)]
            })
            # Notificar al reclutador
            applicant.message_post(
                body="El candidato ha sido bloqueado por no realizar las pruebas psicométricas en el tiempo establecido.",
                subtype_id=self.env.ref('mail.mt_comment').id
            )

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