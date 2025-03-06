from odoo import models, api, fields, _
from odoo.exceptions import UserError
import logging
import re

_logger = logging.getLogger(__name__)

class HrApplicant(models.Model):
    _inherit = 'hr.applicant'

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
    place_of_origin = fields.Char(string="Lugar de Origen y Residencia")
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
    previous_surgeries = fields.Char(string="Cirugías Previas")
    traumas = fields.Char(string="Traumas")
    transfusions = fields.Char(string="Transfusiones")
    allergies = fields.Char(string="Alergias")
    chronic_diseases = fields.Char(string="Enfermedades Crónicas")
    childhood_diseases = fields.Char(string="Enfermedades de la Infancia")
    smoking = fields.Selection([('yes', 'Sí'), ('no', 'No')], string="Tabaquismo")
    alcoholism = fields.Selection([('yes', 'Sí'), ('no', 'No')], string="Alcoholismo")
    drug_addiction = fields.Char(string="Adicción a Drogas")

    # Esquema de Vacunación
    complete_schedule = fields.Selection([('yes', 'Sí'), ('no', 'No')], string="Esquema Completo")
    no_vaccination_card = fields.Boolean(string="Sin Cartilla de Vacunación")
    last_vaccine = fields.Date(string="Última Vacuna")

    # Examen Físico
    heart_rate = fields.Integer(string="Frecuencia Cardíaca (LPM)")
    respiratory_rate = fields.Integer(string="Frecuencia Respiratoria (RPM)")
    temperature = fields.Float(string="Temperatura (°C)")
    blood_pressure = fields.Char(string="Presión Arterial (mmHg)")
    oxygen_saturation = fields.Float(string="Saturación de Oxígeno (%)")
    weight = fields.Float(string="Peso (Kg)")
    height = fields.Float(string="Estatura (Cm)")
    bmi = fields.Float(string="IMC")

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
