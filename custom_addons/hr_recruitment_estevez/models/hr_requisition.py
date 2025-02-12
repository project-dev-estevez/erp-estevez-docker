from odoo import models, fields, api
from odoo.exceptions import ValidationError

class HrRequisition(models.Model):
    _name = 'hr.requisition'
    _description = 'Requisición de Personal'

    state = fields.Selection([
        ('to_approve', 'Para Aprobar'),
        ('approved', 'Aprobado'),
        ('rejected', 'Rechazado'),
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
        ('new_vacancy', 'Nueva vacante'),
        ('other', 'Otro'),
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
    ], string="Tipo de Puesto", required=True)
    workstation_direction_id = fields.Many2one('hr.direction', string="Dirección del Puesto", required=True)
    workstation_department_id = fields.Many2one('hr.department', string="Departamento del Puesto", domain="[('direction_id', '=', workstation_direction_id)]", required=True)
    workstation_job_id = fields.Many2one('hr.job', string="Puesto Solicitado", domain="[('department_id', '=', workstation_department_id)]", required=True)
    project = fields.Char(string="ID de Proyecto")
    number_of_vacancies = fields.Integer(string="Número de Vacantes", default=1)
    work_schedule = fields.Many2one('resource.calendar', string="Horario de Jornada Laboral", required=True)
    gender = fields.Selection([
        ('male', 'Masculino'),
        ('female', 'Femenino'),
        ('other', 'Otro'),
    ], string="Género")
    age_range_min = fields.Integer(string="Edad Mínima", required=True, default=18)
    age_range_max = fields.Integer(string="Edad Máxima", required=True, default=100)
    years_of_experience = fields.Integer(string="Años de Experiencia", required=True)
    general_functions = fields.Text(string="Funciones Generales del Puesto")
    academic_degree_id = fields.Many2one('hr.recruitment.degree', string="Escolaridad o Grado Académico", required=True)
    software_ids = fields.Many2many('hr.requisition.software', string="Software que se utilizará por el empleado")

    # Equipo requerido
    computer_equipment_required = fields.Boolean(string="¿Requiere Equipo de Cómputo?", default=False)
    cellular_equipment_required = fields.Boolean(string="¿Requiere Equipo Celular?", default=False)
    uniform_ids = fields.Many2many('hr.requisition.uniform', string="Uniformes")
    epp_ids = fields.Many2many('hr.requisition.epp', string="Equipo de Protección Personal")

    _sql_constraints = [
        ('check_years_of_experience', 'CHECK(years_of_experience >= 0)', 'Los años de experiencia no pueden ser un número negativo.')
    ]

    # Acciones de estado
    def action_submit_for_approval(self):
        self.state = 'to_approve'

    def action_approve(self):
        self.state = 'approved'

    def action_reject(self):
        self.state = 'rejected'

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
