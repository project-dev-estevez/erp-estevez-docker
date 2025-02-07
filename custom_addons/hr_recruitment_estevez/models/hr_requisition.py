from odoo import models, fields, api
from odoo.exceptions import ValidationError

class HrRequisition(models.Model):
    _name = 'hr.requisition'
    _description = 'Requisición de Personal'

    state = fields.Selection([
        ('draft', 'Borrador'),
        ('to_approve', 'Para Aprobar'),
        ('approved', 'Aprobado'),
        ('rejected', 'Rechazado'),
    ], string="Estado", default='draft')

    # Información del solicitante
    requisition_number = fields.Char(string='Formato de Solicitud', readonly=True, default='DA-F0-TH-006')
    requestor_id = fields.Many2one('res.users', string="Solicitante", default=lambda self: self.env.user, required=True, readonly=True)
    establishment = fields.Selection([
        ('estevez_jor', 'Estevez.Jor'),
        ('kuali_digital', 'Kuali Digital'),
        ('fundidora', 'Fundidora'),
        ('vigiliner', 'Vigiliner'),
    ], string="Establecimiento", required=True)
    direction_id = fields.Many2one('hr.direction', string="Dirección", required=True)
    department_id = fields.Many2one('hr.department', string="Departamento", domain="[('direction_id', '=', direction_id)]", required=True)
    job_id = fields.Many2one('hr.job', string="Puesto Solicitado", domain="[('department_id', '=', department_id)]", required=True)

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
        ('administrative', 'Administrative'),
        ('operational', 'Operational'),
    ], string="Tipo de Puesto", required=True)
    workstation_direction_id = fields.Many2one('hr.direction', string="Dirección del Puesto", required=True)
    workstation_department_id = fields.Many2one('hr.department', string="Departamento del Puesto", domain="[('direction_id', '=', workstation_direction_id)]", required=True)
    workstation_job_id = fields.Many2one('hr.job', string="Puesto a Cubrir", domain="[('department_id', '=', workstation_department_id)]", required=True)
    project = fields.Char(string="ID de Proyecto")
    number_of_vacancies = fields.Integer(string="Número de Vacantes", default=1)
    work_schedule = fields.Many2one('resource.calendar', string="Horario de Jornada Laboral", required=True)
    gender = fields.Selection([
        ('male', 'Masculino'),
        ('female', 'Femenino'),
        ('other', 'Otro'),
    ], string="Género")
    age_range = fields.Char(string="Rango de Edad", required=True)
    years_of_experience = fields.Integer(string="Años de Experiencia", required=True)
    general_functions = fields.Text(string="Funciones Generales del Puesto")
    academic_degree_id = fields.Many2one('hr.recruitment.degree', string="Grado Académico", required=True)
    software_to_use = fields.Char(string="Software a Utilizar", required=True)

    # Equipo requerido
    computer_equipment_required = fields.Boolean(string="¿Requiere Equipo de Cómputo?", default=False)
    cellular_equipment_required = fields.Boolean(string="¿Requiere Equipo Celular?", default=False)
    uniform_ids = fields.Many2many('hr.requisition.uniform', string="Uniformes")
    epp_ids = fields.Many2many('hr.requisition.epp', string="EPP")
    other_epp_description = fields.Text(string="Descripción de Otro EPP")

    # Acciones de estado
    def action_submit_for_approval(self):
        self.state = 'to_approve'

    def action_approve(self):
        self.state = 'approved'

    def action_reject(self):
        self.state = 'rejected'

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

    # Si se selecciona "Otro" en EPP, se debe habilitar el campo de descripción
    @api.onchange('epp_ids')
    def _onchange_epp_ids(self):
        other_epp = self.env.ref('hr_recruitment_estevez.epp_otro', raise_if_not_found=False)
        if other_epp and other_epp in self.epp_ids:
            self.other_epp_description = True
        else:
            self.other_epp_description = False