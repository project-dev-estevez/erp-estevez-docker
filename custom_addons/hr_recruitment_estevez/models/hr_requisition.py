import logging
from odoo import models, fields, api
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

class HrRequisition(models.Model):
    _name = 'hr.requisition'
    _description = 'Requisición de Personal'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'

    name = fields.Char(string="Nombre", compute="_compute_name", store=True)
    workstation_job_id = fields.Many2one('hr.job', string="Puesto")

    wizard_step = fields.Selection(
        selection=[
            ('especificaciones', 'Especificaciones de Requisición'),
            ('datos_puesto', 'Datos del puesto'),
            ('equipo', 'Equipo requerido')
        ],
        string='Paso actual',
        default='especificaciones'
    )

    state = fields.Selection([
        ('to_approve', 'Por Aprobar'),
        ('first_approval', 'En Curso'),
        ('rejected', 'Rechazado'),
        ('approved', 'Aprobado'),
    ], string="Estado", default='to_approve', track_visibility='onchange')

    requisition_number = fields.Char(string='Formato de Solicitud', readonly=True, default='DA-F0-TH-006')
    # Información del solicitante
    requestor_id = fields.Many2one('res.users', string="Solicitante", default=lambda self: self.env.user, readonly=True)
    company_id = fields.Many2one('res.company', string="Empresa", related='requestor_id.company_id', readonly=True, store=False)
    direction_id = fields.Many2one('hr.direction', string="Dirección", related='requestor_id.employee_id.direction_id', readonly=True, store=False)
    department_id = fields.Many2one('hr.department', string="Departamento", related='requestor_id.employee_id.department_id', readonly=True, store=False)
    job_id = fields.Many2one('hr.job', string="Puesto Solicitante", related='requestor_id.employee_id.job_id', readonly=True, store=False)

    # Especificaciones de la requisición
    requisition_type = fields.Selection([
        ('new_creation', 'Puesto de nueva creación'),
        ('replacement', 'Reposición de personal'),
        ('new_vacancy', 'Nueva vacante')
    ], string="Tipo de Requisición", help="Tipo de solicitud")
    employee_id = fields.Many2one('hr.employee', string="Empleado a Reemplazar")
    vacancy_reason = fields.Selection([
        ('voluntary_retirement', 'Retiro Voluntario'),
        ('contract_cancellation', 'Cancelación de Contrato'),
        ('maternity_leave', 'Licencia por Maternidad'),
        ('contract_termination', 'Terminación de Contrato'),
        ('promotion', 'Promoción'),
        ('retirement', 'Jubilación'),
        ('other', 'Otro'),
    ], string="Motivo de Vacante")
    other_reason_description = fields.Text(string="Descripción de Otro Motivo")
    
    # Información del puesto
    job_type = fields.Selection([
        ('administrative', 'Administrativo'),
        ('operational', 'Operativo'),
    ], string="Tipo de Puesto", help="Selecciona el tipo de funciones que desempeñará el puesto. Administrativo: (Oficina, planificación o soporte interno). Operativo: (Tareas técnicas o de campo).")
    workstation_direction_id = fields.Many2one('hr.direction', string="Dirección del Puesto", help="Selecciona la dirección a la que pertenece el puesto dentro de la empresa.")
    workstation_department_id = fields.Many2one('hr.department', string="Departamento del Puesto", domain="[('direction_id', '=', workstation_direction_id)]", help="Indica el departamento específico al que está adscrito el puesto.")
    workstation_area_id = fields.Many2one('hr.area', string="Área del Puesto", domain="[('department_id', '=', workstation_department_id)]", help="Especifica el área interna donde el puesto realiza sus funciones.")
    workstation_job_id = fields.Many2one('hr.job', string="Puesto Solicitado", domain="[('department_id', '=', workstation_department_id)]", help="Nombre del puesto que se solicita cubrir.")
    project_id = fields.Many2one('project.project', string="Proyecto", help="Especifica el proyecto al que estará asignado el puesto.")
    number_of_vacancies = fields.Integer(string="Número de Vacantes", help="Número total de puestos disponibles que se desean cubrir.")
    work_schedule = fields.Many2one('resource.calendar', string="Horario de Jornada Laboral", help="Selecciona el tipo de jornada laboral correspondiente.")
    gender = fields.Selection([
        ('male', 'Masculino'),
        ('female', 'Femenino'),
        ('indistinct', 'Indistinto'),
        ('other', 'Otro')
    ], string="Género", help="Selecciona el género requerido para el puesto.")
    
    age_range_min = fields.Selection(
        selection=[(str(i), str(i)) for i in range(18, 61)],  # 18 a 60
        string="Edad Mínima",
        default='18'
    )

    age_range_max = fields.Selection(
        selection=[(str(i), str(i)) for i in range(60, 17, -1)],
        string="Edad Máxima",
        default='60'
    )
        
    #age_range_min = fields.Integer(string="Edad Mínima", default=18)
    # age_range_max = fields.Integer(string="Edad Máxima", default=60)
    #years_of_experience = fields.Integer(string="Años de Experiencia", required=True, help="Indica los años mínimos de experiencia que debe tener el candidato.")
    years_of_experience = fields.Selection([
        ('seis_meses', '6 meses'),
        ('uno_anio', '1 año'),
        ('dos_anios', '2 años'),
        ('tres_anios', '3 años'),
        ('cuatro_anios', '4 años'),
        ('cinco_anios', '5 años'),
        ('seis_anios', '6 años en adelante')
    ], string="Años de Experiencia", help="Indica los años mínimos de experiencia que debe tener el candidato.")
    general_functions = fields.Text(string="Funciones Generales del Puesto", help="Especifica las tareas generales del puesto.")
    academic_degree_id = fields.Many2one('hr.recruitment.degree', string="Escolaridad o Grado Académico", help="Selecciona el nivel educativo requerido.")
    software_ids = fields.Many2many('hr.requisition.software', string="Software que se utilizará por el empleado", help="Menciona los programas que el empleado debe utilizar.")

    # Equipo requerido
    computer_equipment_required = fields.Boolean(string="¿Requiere Equipo de Cómputo?", default=False, help="Indica si requiere que se le asigne algún equipo.")
    cellular_equipment_required = fields.Boolean(string="¿Requiere Equipo Celular?", default=False, help="Indica si se requiere que se le asigne algun celular.")
    uniform_ids = fields.Many2many('hr.requisition.uniform', string="Uniformes", help="Indica si requiere que se le asigne algun uniforme.")
    epp_ids = fields.Many2many('hr.requisition.epp', string="Equipo de Protección Personal", help="Indica si requiere que se le asigne equipo de protección personal.")

    # Tags de la requisición
    tag_ids = fields.Many2many('hr.requisition.tag', string="Etiquetas")
    observations = fields.Text(string="Observaciones de la Vacante", help="Espacio para incluir comentarios adicionales o detalles relevantes sobre la vacante.")

    is_published = fields.Boolean(
        string='Vacante Publicada',
        default=False,
        copy=False,
        tracking=True
    )
    publish_date = fields.Datetime(
        string='Fecha de Publicación',
        copy=False
    )
    close_date = fields.Datetime(
        string='Fecha de Cierre',
        copy=False
    )

    _sql_constraints = [
        ('check_years_of_experience', 'CHECK(years_of_experience >= 0)', 'Los años de experiencia no pueden ser un número negativo.')
    ]

    # Nuevo campo computado
    publication_status = fields.Char(
        string='Estado Publicación',
        compute='_compute_publication_status',
        store=False
    )    

    @api.constrains('wizard_step', 'job_type', '')

    @api.depends('workstation_job_id')
    def _compute_name(self):
        for record in self:
            record.name = f"Requisición - {record.workstation_job_id.name or 'Sin Puesto'}"
    
    @api.depends('state', 'is_published')
    def _compute_publication_status(self):
        for record in self:
            if record.state != 'approved':
                record.publication_status = 'Por Activar'
            else:
                record.publication_status = 'Abierta' if record.is_published else 'Cerrada'

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


    def action_reset_to_draft(self):
        for record in self:
            # Solo permite restablecer si está aprobado o rechazado
            if record.state in ['approved', 'rejected']:
                # Volver al estado inicial (ajusta según tu flujo)
                record.state = 'to_approve'
                
                # Opcional: Resetear campos relacionados
                record.is_published = False
    
        return True
    
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
            # Convertir a enteros
            min_age = int(record.age_range_min) if record.age_range_min else 0
            max_age = int(record.age_range_max) if record.age_range_max else 0
        
            if min_age < 18:
                raise ValidationError("La edad mínima no puede ser menor a 18 años")
            
            if max_age <= min_age:
                raise ValidationError("La edad máxima debe ser mayor que la mínima")
            
            if max_age > 60:
                raise ValidationError("La edad máxima no puede exceder los 60 años")

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
        # Crear acción de retorno
        action = {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'views': [(False, 'form')],
            'target': 'current',
        }
        
        return {
        'effect': {
            'type': 'rainbow_man',
            'message': '¡Requisición completada exitosamente!',
            'fadeout': 'slow',
            'next': {
                'type': 'ir.actions.act_window',
                'res_model': self._name,
                'res_id': self.id,
                'views': [(False, 'form')],
                'target': 'current',
            }
        }
    }
    
    def action_previous(self):
        steps = {
            'datos_puesto': 'especificaciones',
            'equipo': 'datos_puesto'
        }
        for record in self:
            record.wizard_step = steps.get(record.wizard_step, 'especificaciones')
        return False
    
    def action_next(self):
        # Validación de paso actual
        error_messages = {
            'especificaciones': "Debe completar todos los campos obligatorios en 'Especificaciones'",
            'datos_puesto': "Faltan datos importantes en 'Datos del puesto'"
        }
        
        # Aquí puedes agregar validaciones específicas por paso
        # Por ejemplo, si en el paso 'especificaciones' hay un campo obligatorio:
        if self.wizard_step == 'especificaciones':
            if not self.requisition_type:  # Reemplaza con tu campo real
                raise UserError(error_messages['especificaciones'])
        elif self.wizard_step == 'datos_puesto':
            if not self.job_type:  # Reemplaza con tu campo real
                raise UserError(error_messages['datos_puesto'])
        
        steps = {
            'especificaciones': 'datos_puesto',
            'datos_puesto': 'equipo'
        }
        for record in self:
            record.wizard_step = steps.get(record.wizard_step, 'equipo')
        return False
    
    def set_wizard_step(self, step):
        self.ensure_one()
        valid_steps = ['especificaciones', 'datos_puesto', 'equipo']
        if step in valid_steps:
            self.wizard_step = step
        return True
    
    def action_publish_vacancy(self):
        self.ensure_one()
        
        if self.state != 'approved':
            raise UserError("Solo puedes publicar vacantes aprobadas")
        
        if self.is_published:
            raise UserError("La vacante ya está publicada")
        
        # Actualizar la requisición
        self.write({
            'is_published': True,
            'publish_date': fields.Datetime.now(),
            'close_date': False
        })
        
        # Actualizar el puesto de trabajo asociado
        if self.workstation_job_id:
            self.workstation_job_id.write({
                'is_published': True,
            
            })
        
        # Notificación con recarga automática
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Vacante Publicada',
                'message': 'La vacante ha sido aperturada correctamente',
                'sticky': False,
                'type': 'success',
                'next': {
                    'type': 'ir.actions.act_window',
                    'res_model': self._name,
                    'res_id': self.id,
                    'views': [(False, 'form')],
                    'target': 'current',
                }
            }
        }

    def action_close_vacancy(self):
        self.ensure_one()
        
        if not self.is_published:
            raise UserError("La vacante no está publicada")
        
        # Actualizar la requisición
        self.write({
            'is_published': False,
            'close_date': fields.Datetime.now()
        })
        
        # Actualizar el puesto de trabajo asociado
        if self.workstation_job_id:
            self.workstation_job_id.write({
                'is_published': False,
                
            })
        
        # Notificación con recarga automática
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Vacante Cerrada',
                'message': 'La vacante ha sido cerrada correctamente',
                'sticky': False,
                'type': 'warning',
                'next': {
                    'type': 'ir.actions.act_window',
                    'res_model': self._name,
                    'res_id': self.id,
                    'views': [(False, 'form')],
                    'target': 'current',
                }
            }
        }