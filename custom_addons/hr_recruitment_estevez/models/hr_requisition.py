import logging
from odoo import models, fields, api
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

class HrRequisition(models.Model):
    _name = 'hr.requisition'
    _description = 'Requisición de Personal'
    _inherit = ['mail.thread']

    state = fields.Selection([
        ('to_approve', 'Por Aprobar'),
        ('first_approval', 'En Curso'),
        ('rejected', 'Rechazado'),
        ('approved', 'Aprobado'),
    ], string="Estado", default='to_approve')

    requisition_number = fields.Char(string='Formato de Solicitud', readonly=True, default='DA-F0-TH-006')
    # Información del solicitante
    requestor_id = fields.Many2one('res.users', string="Solicitante", default=lambda self: self.env.user, required=True, readonly=True)
    company_id = fields.Many2one('res.company', string="Empresa", related='requestor_id.company_id', readonly=True, store=False)
    direction_id = fields.Many2one('hr.direction', string="Dirección", related='requestor_id.employee_id.direction_id', readonly=True, store=False)
    department_id = fields.Many2one('hr.department', string="Departamento", related='requestor_id.employee_id.department_id', readonly=True, store=False)
    job_id = fields.Many2one('hr.job', string="Puesto Solicitante", related='requestor_id.employee_id.job_id', readonly=True, store=False)

    # Especificaciones de la requisición
    requisition_type = fields.Selection([
        ('new_creation', 'Puesto de nueva creación'),
        ('replacement', 'Reposición de personal'),
        ('new_vacancy', 'Nueva vacante')
    ], string="Tipo de Requisición", required=True)
    employee_id = fields.Many2one('hr.employee', string="Empleado a Reemplazar")
    vacancy_reason = fields.Selection([
        ('voluntary_retirement', 'Retiro Voluntario'),
        ('contract_cancellation', 'Cancelación de Contrato'),
        ('maternity_leave', 'Licencia por Maternidad'),
        ('contract_termination', 'Terminación de Contrato'),
        ('promotion', 'Promoción'),
        ('retirement', 'Jubilación'),
        ('other', 'Otro'),
    ], string="Motivo de Vacante", required=True)
    other_reason_description = fields.Text(string="Descripción de Otro Motivo")
    
    # Información del puesto
    job_type = fields.Selection([
        ('administrative', 'Administrativo'),
        ('operational', 'Operativo'),
    ], string="Tipo de Puesto")
    workstation_direction_id = fields.Many2one('hr.direction', string="Dirección del Puesto")
    workstation_department_id = fields.Many2one('hr.department', string="Departamento del Puesto", domain="[('direction_id', '=', workstation_direction_id)]")
    workstation_area_id = fields.Many2one('hr.area', string="Área del Puesto", domain="[('department_id', '=', workstation_department_id)]")
    workstation_job_id = fields.Many2one('hr.job', string="Puesto Solicitado", domain="[('department_id', '=', workstation_department_id)]")
    project_id = fields.Many2one('project.project', string="Proyecto")
    number_of_vacancies = fields.Integer(string="Número de Vacantes")
    work_schedule = fields.Many2one('resource.calendar', string="Horario de Jornada Laboral")
    gender = fields.Selection([
        ('male', 'Masculino'),
        ('female', 'Femenino'),
        ('indistinct', 'Indistinto'),
        ('other', 'Otro')
    ], string="Género")
    age_range_min = fields.Integer(string="Edad Mínima", required=True, default=18)
    age_range_max = fields.Integer(string="Edad Máxima", required=True, default=60)
    years_of_experience = fields.Integer(string="Años de Experiencia", required=True)
    general_functions = fields.Text(string="Funciones Generales del Puesto")
    academic_degree_id = fields.Many2one('hr.recruitment.degree', string="Escolaridad o Grado Académico")
    software_ids = fields.Many2many('hr.requisition.software', string="Software que se utilizará por el empleado")

    # Equipo requerido
    computer_equipment_required = fields.Boolean(string="¿Requiere Equipo de Cómputo?", default=False)
    cellular_equipment_required = fields.Boolean(string="¿Requiere Equipo Celular?", default=False)
    uniform_ids = fields.Many2many('hr.requisition.uniform', string="Uniformes")
    epp_ids = fields.Many2many('hr.requisition.epp', string="Equipo de Protección Personal")

    # Tags de la requisición
    tag_ids = fields.Many2many('hr.requisition.tag', string="Etiquetas")
    observations = fields.Text(string="Observaciones de la Vacante")

    _sql_constraints = [
        ('check_years_of_experience', 'CHECK(years_of_experience >= 0)', 'Los años de experiencia no pueden ser un número negativo.')
    ]

    # Acciones de estado
    def action_approve(self):
        self.state = 'first_approval'
        
        if not self.direction_id:
            _logger.warning("No direction ID found for the requisition")
            return

        _logger.info("Direction ID found: %s", self.direction_id.id)
        if not self.direction_id.director_id:
            _logger.warning("No director ID found for direction ID: %s", self.direction_id.id)
            return

        _logger.info("Director ID found: %s", self.direction_id.director_id.id)
        director_user = self.direction_id.director_id.user_id
        if not director_user:
            _logger.warning("No director user found for director ID: %s", self.direction_id.director_id.id)
            return

        _logger.info("Director user found: %s", director_user.id)
        if not director_user.employee_id or not director_user.employee_id.parent_id:
            _logger.warning("No immediate supervisor found for director user ID: %s", director_user.id)
            return

        immediate_supervisor_user = director_user.employee_id.parent_id.user_id
        if not immediate_supervisor_user:
            _logger.warning("No user found for immediate supervisor of director user ID: %s", director_user.id)
            return

        _logger.info("Immediate supervisor user found: %s", immediate_supervisor_user.id)
        message = "La requisición de personal ha sido aprobada por %s." % self.requestor_id.name
        subject = "Requisición Aprobada: %s" % self.requisition_number
        message_id = self.message_post(
            body=message,
            subject=subject,
            partner_ids=[immediate_supervisor_user.partner_id.id],
            message_type='notification',
            subtype_xmlid='mail.mt_comment',
        )
        _logger.info("Notification sent to immediate supervisor user: %s", immediate_supervisor_user.partner_id.id)
        _logger.info("Message ID: %s", message_id)

    def action_confirm_approve(self):
        if self.state == 'first_approval':
            self.state = 'approved'
            
            if not self.direction_id:
                _logger.warning("No direction ID found for the requisition")
                return

            _logger.info("Direction ID found: %s", self.direction_id.id)
            if not self.direction_id.director_id:
                _logger.warning("No director ID found for direction ID: %s", self.direction_id.id)
                return

            _logger.info("Director ID found: %s", self.direction_id.director_id.id)
            director_user = self.direction_id.director_id.user_id
            if not director_user:
                _logger.warning("No director user found for director ID: %s", self.direction_id.director_id.id)
                return

            _logger.info("Director user found: %s", director_user.id)
            message = "La requisición de personal ha sido aprobada por %s." % self.requestor_id.name
            subject = "Requisición Aprobada: %s" % self.requisition_number
            partner_ids = [director_user.partner_id.id, self.requestor_id.partner_id.id]
            message_id = self.message_post(
                body=message,
                subject=subject,
                partner_ids=partner_ids,
                message_type='notification',
                subtype_xmlid='mail.mt_comment',
            )
            _logger.info("Notification sent to director user: %s and requestor user: %s", director_user.partner_id.id, self.requestor_id.partner_id.id)
            _logger.info("Message ID: %s", message_id)

    def action_reject(self):
        self.state = 'rejected'
        partner_ids = [self.requestor_id.partner_id.id]
        
        if self.state == 'first_approval' and self.direction_id and self.direction_id.director_id:
            director_user = self.direction_id.director_id.user_id
            if director_user and director_user.partner_id:
                partner_ids.append(director_user.partner_id.id)
        
        if not partner_ids:
            _logger.warning("No partner IDs found for notification")
            return

        message = "Su solicitud de requisición de personal ha sido rechazada."
        subject = "Requisición Rechazada: %s" % self.requisition_number
        message_id = self.message_post(
            body=message,
            subject=subject,
            partner_ids=partner_ids,
            message_type='notification',
            subtype_xmlid='mail.mt_comment',
        )
        if message_id:
            _logger.info("Notification sent to partner IDs: %s", partner_ids)
            _logger.info("Message ID: %s", message_id)
        else:
            _logger.warning("Failed to send notification to partner IDs: %s", partner_ids)

    @api.constrains('age_range_min', 'age_range_max')
    def _check_age_range(self):
        for record in self:
            if record.age_range_min < 18:
                raise ValidationError("La edad mínima debe ser al menos 18 años.")
            if record.age_range_max > 100:
                raise ValidationError("La edad máxima debe ser como máximo 100 años.")
            if record.age_range_min > record.age_range_max:
                raise ValidationError("La edad mínima no puede ser mayor que la edad máxima.")

    # Si es para un reemplazo se debe de seleccionar el empleado a reemplazar
    @api.constrains('requisition_type', 'employee_id')
    def _check_employee_id_required(self):
        for record in self:
            if record.requisition_type == 'replacement' and not record.employee_id:
                raise ValidationError("Debe seleccionar el empleado a reemplazar cuando el tipo de requisición es 'Reposición de personal'.")

    # Si la vacante es por otro motivo se debe de especificar cual es
    @api.constrains('vacancy_reason', 'other_reason_description')
    def _check_other_reason_description(self):
        for record in self:
            if record.vacancy_reason == 'other' and not record.other_reason_description:
                raise ValidationError("Debe especificar la descripción del otro motivo cuando el motivo de la vacante es 'Otro'.")

    @api.model
    def create(self, vals):
        _logger.info("Creating a new hr.requisition record with values: %s", vals)
        record = super(HrRequisition, self).create(vals)
        _logger.info("New hr.requisition record created with ID: %s", record.id)

        if not record.direction_id:
            _logger.warning("No direction ID found for the requisition")
            return record

        _logger.info("Direction ID found: %s", record.direction_id.id)
        if not record.direction_id.director_id:
            _logger.warning("No director ID found for direction ID: %s", record.direction_id.id)
            return record

        _logger.info("Director ID found: %s", record.direction_id.director_id.id)
        director_user = record.direction_id.director_id.user_id
        if not director_user:
            _logger.warning("No director user found for director ID: %s", record.direction_id.director_id.id)
            return record

        _logger.info("Director user found: %s", director_user.id)
        message = "Se ha creado una nueva requisición de personal por el usuario %s." % record.requestor_id.name
        subject = "Nueva Requisición: %s" % record.requisition_number
        message_id = record.message_post(
            body=message,
            subject = subject,
            partner_ids=[director_user.partner_id.id],
            message_type='notification',
            subtype_xmlid='mail.mt_comment',
        )
        _logger.info("Notification sent to director user: %s", director_user.partner_id.id)
        _logger.info("Message ID: %s", message_id)

        return record
    
    def action_save(self):
        # Aquí puedes agregar cualquier lógica adicional antes de guardar
        self.ensure_one()
        self.write({'state': self.state})  # Esto guarda el registro
        _logger.info("Requisición guardada con éxito")
        return True