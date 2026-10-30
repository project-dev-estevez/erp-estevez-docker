import logging
from markupsafe import Markup
from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError

_logger = logging.getLogger(__name__)

WIZARD_STEPS = ['especificaciones', 'datos_puesto', 'equipo']


class HrRequisition(models.Model):
    _name = 'hr.requisition'
    _description = 'Requisición de Personal'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'
    _order = 'create_date desc, id desc'

    folio = fields.Char(string="Folio", readonly=True, copy=False, index=True)
    name = fields.Char(string="Nombre", compute="_compute_name", store=True)

    wizard_step = fields.Selection(
        selection=[
            ('especificaciones', 'Especificaciones de Requisición'),
            ('datos_puesto', 'Datos del puesto'),
            ('equipo', 'Equipo requerido')
        ],
        string='Paso actual',
        default='especificaciones'
    )

    # Flujo: Borrador → Aprobación de Dirección → Aprobación final → Aprobada (o Rechazada)
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('to_approve', 'Aprobación Dirección'),
        ('first_approval', 'Aprobación Final'),
        ('rejected', 'Rechazada'),
        ('approved', 'Aprobada'),
    ], string="Estado", default='draft', tracking=True, copy=False)

    requisition_number = fields.Char(string='Formato de Solicitud', readonly=True, default='DA-F0-TH-006')
    # Información del solicitante
    requestor_id = fields.Many2one('res.users', string="Solicitante", default=lambda self: self.env.user, readonly=True)
    company_id = fields.Many2one('res.company', string="Empresa", related='requestor_id.company_id', readonly=True, store=False)
    direction_id = fields.Many2one('hr.direction', string="Dirección", related='requestor_id.employee_id.direction_id', readonly=True, store=False)
    department_id = fields.Many2one('hr.department', string="Área", related='requestor_id.employee_id.department_id', readonly=True, store=False)
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
    workstation_department_id = fields.Many2one('hr.department', string="Área del Puesto", domain="[('direction_id', '=', workstation_direction_id)]", help="Indica el área específica a la que está adscrito el puesto.")
    workstation_area_id = fields.Many2one('hr.area', string="Departamento del Puesto", domain="[('department_id', '=', workstation_department_id)]", help="Especifica el departamento interno donde el puesto realiza sus funciones.")
    workstation_job_id = fields.Many2one('hr.job', string="Puesto Solicitado", domain="[('department_id', '=', workstation_department_id)]", help="Nombre del puesto que se solicita cubrir.")
    project_id = fields.Many2one('project.project', string="Proyecto", help="Especifica el proyecto al que estará asignado el puesto.")
    number_of_vacancies = fields.Integer(string="Número de Vacantes", default=1, help="Número total de puestos disponibles que se desean cubrir.")
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

    year_of_experience = fields.Selection([
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

    # Aprobaciones
    submit_date = fields.Datetime(string="Enviada a aprobación", readonly=True, copy=False)
    first_approver_id = fields.Many2one('res.users', string="Aprobó Dirección", readonly=True, copy=False)
    first_approval_date = fields.Datetime(string="Fecha aprobación Dirección", readonly=True, copy=False)
    final_approver_id = fields.Many2one('res.users', string="Aprobación final", readonly=True, copy=False)
    final_approval_date = fields.Datetime(string="Fecha aprobación final", readonly=True, copy=False)
    rejected_by_id = fields.Many2one('res.users', string="Rechazó", readonly=True, copy=False)
    rejection_reason = fields.Text(string="Motivo de rechazo", readonly=True, copy=False, tracking=True)

    pending_approver_id = fields.Many2one('res.users', string="Pendiente de aprobar por", compute='_compute_approval_info')
    is_current_approver = fields.Boolean(compute='_compute_approval_info')
    is_requestor = fields.Boolean(compute='_compute_approval_info')

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

    publication_status = fields.Char(
        string='Estado Vacante',
        compute='_compute_publication_status',
        store=False,
        search='_search_publication_status'
    )

    # ------------------------------------------------------------------
    # Cómputos
    # ------------------------------------------------------------------

    @api.depends('folio', 'workstation_job_id')
    def _compute_name(self):
        for record in self:
            job_name = record.workstation_job_id.name or 'Sin puesto'
            record.name = f"{record.folio} · {job_name}" if record.folio else f"Requisición · {job_name}"

    @api.depends('state', 'is_published')
    def _compute_publication_status(self):
        for record in self:
            if record.state == 'rejected':
                record.publication_status = 'No aplica'
            elif record.state != 'approved':
                record.publication_status = 'Por Abrir'
            else:
                record.publication_status = 'Abierta' if record.is_published else 'Cerrada'

    def _search_publication_status(self, operator, value):
        if operator not in ('=', '!=', 'ilike', 'not ilike', 'in', 'not in'):
            return []

        status_mapping = {
            'Por Abrir': [('state', 'in', ('draft', 'to_approve', 'first_approval'))],
            'Abierta': [('state', '=', 'approved'), ('is_published', '=', True)],
            'Cerrada': [('state', '=', 'approved'), ('is_published', '=', False)],
            'No aplica': [('state', '=', 'rejected')],
        }

        if value in status_mapping:
            return status_mapping[value]

        return []

    @api.depends_context('uid')
    @api.depends('state', 'requestor_id')
    def _compute_approval_info(self):
        user = self.env.user
        is_recruitment_manager = user.has_group('hr_recruitment.group_hr_recruitment_manager')
        for record in self:
            approver = record._get_pending_approver()
            record.pending_approver_id = approver
            record.is_requestor = record.requestor_id == user
            if record.state not in ('to_approve', 'first_approval'):
                record.is_current_approver = False
            elif approver:
                record.is_current_approver = approver == user
            else:
                # Sin aprobador configurado: Talento Humano puede aprobar para que no se atore
                record.is_current_approver = is_recruitment_manager

    # ------------------------------------------------------------------
    # Aprobadores
    # ------------------------------------------------------------------

    def _get_director_employee(self):
        # sudo: un colaborador sin permisos de RH no puede leer la ficha privada del Director
        self.ensure_one()
        return self.sudo().direction_id.director_id

    def _get_first_approver(self):
        """1ª aprobación: Director de la Dirección del solicitante."""
        self.ensure_one()
        return self._get_director_employee().user_id.with_env(self.env)

    def _get_final_approver(self):
        """2ª aprobación: jefe inmediato del Director."""
        self.ensure_one()
        return self._get_director_employee().parent_id.user_id.with_env(self.env)

    def _get_pending_approver(self):
        self.ensure_one()
        if self.state == 'to_approve':
            return self._get_first_approver()
        if self.state == 'first_approval':
            return self._get_final_approver()
        return self.env['res.users']

    def _check_current_approver(self):
        for record in self:
            if not record.is_current_approver:
                approver = record.pending_approver_id
                raise UserError(
                    f"Esta requisición la debe aprobar {approver.name}." if approver
                    else "No tienes permiso para aprobar esta requisición."
                )

    def _schedule_approval_activity(self, user):
        self.ensure_one()
        if user:
            self.activity_schedule(
                'mail.mail_activity_data_todo',
                user_id=user.id,
                summary="Aprobar requisición de personal",
                note=f"Revisa y aprueba o rechaza la requisición {self.name}.",
            )

    def _close_approval_activities(self, feedback):
        self.activity_feedback(['mail.mail_activity_data_todo'], feedback=feedback)

    def _notify(self, body, partners):
        self.message_post(
            body=body,
            partner_ids=partners.ids,
            message_type='comment',
            subtype_xmlid='mail.mt_comment',
        )

    # ------------------------------------------------------------------
    # Validaciones
    # ------------------------------------------------------------------

    @api.constrains('age_range_min', 'age_range_max')
    def _check_age_range(self):
        for record in self:
            min_age = int(record.age_range_min) if record.age_range_min else 0
            max_age = int(record.age_range_max) if record.age_range_max else 0

            if min_age < 18:
                raise ValidationError("La edad mínima no puede ser menor a 18 años")

            if max_age <= min_age:
                raise ValidationError("La edad máxima debe ser mayor que la mínima")

            if max_age > 60:
                raise ValidationError("La edad máxima no puede exceder los 60 años")

    @api.constrains('requisition_type', 'employee_id')
    def _check_employee_id_required(self):
        for record in self:
            if record.requisition_type == 'replacement' and not record.employee_id:
                raise ValidationError("Debe seleccionar el empleado a reemplazar cuando el tipo de requisición es 'Reposición de personal'.")

    @api.constrains('vacancy_reason', 'other_reason_description')
    def _check_other_reason_description(self):
        for record in self:
            if record.vacancy_reason == 'other' and not record.other_reason_description:
                raise ValidationError("Debe especificar la descripción del otro motivo cuando el motivo de la vacante es 'Otro'.")

    def _missing_fields(self, step):
        """Etiquetas de los campos obligatorios que faltan en un paso."""
        self.ensure_one()
        required = {
            'especificaciones': ['requisition_type'],
            'datos_puesto': [
                'job_type', 'workstation_direction_id', 'workstation_department_id', 'workstation_job_id',
            ],
            'equipo': [],
        }[step]
        missing = [self._fields[name].string for name in required if not self[name]]
        if step == 'datos_puesto' and self.number_of_vacancies < 1:
            missing.append(self._fields['number_of_vacancies'].string)
        return missing

    def _check_step(self, step):
        for record in self:
            missing = record._missing_fields(step)
            if missing:
                raise ValidationError("Completa los campos obligatorios:\n• " + "\n• ".join(missing))

    # ------------------------------------------------------------------
    # Cambios en el formulario
    # ------------------------------------------------------------------

    @api.onchange('workstation_direction_id')
    def _onchange_workstation_direction_id(self):
        if self.workstation_department_id.direction_id != self.workstation_direction_id:
            self.workstation_department_id = False

    @api.onchange('workstation_department_id')
    def _onchange_workstation_department_id(self):
        if self.workstation_area_id.department_id != self.workstation_department_id:
            self.workstation_area_id = False
        if self.workstation_job_id.department_id != self.workstation_department_id:
            self.workstation_job_id = False

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        # En una reposición, el puesto a cubrir es el del empleado que se va
        employee = self.employee_id
        if employee and not self.workstation_job_id:
            self.workstation_direction_id = employee.direction_id
            self.workstation_department_id = employee.department_id
            self.workstation_job_id = employee.job_id

    # ------------------------------------------------------------------
    # Asistente de captura (solo en Borrador)
    # ------------------------------------------------------------------

    def action_previous(self):
        for record in self:
            index = WIZARD_STEPS.index(record.wizard_step or 'especificaciones')
            record.wizard_step = WIZARD_STEPS[max(index - 1, 0)]
        return True

    def action_next(self):
        for record in self:
            step = record.wizard_step or 'especificaciones'
            record._check_step(step)
            index = WIZARD_STEPS.index(step)
            record.wizard_step = WIZARD_STEPS[min(index + 1, len(WIZARD_STEPS) - 1)]
        return True

    def action_go_to_step(self):
        """Clic en el encabezado de un paso: se puede regresar libremente, avanzar solo con lo previo completo."""
        step = self.env.context.get('wizard_step')
        if step not in WIZARD_STEPS:
            return True
        for record in self:
            target = WIZARD_STEPS.index(step)
            for previous in WIZARD_STEPS[:target]:
                record._check_step(previous)
            record.wizard_step = step
        return True

    def set_wizard_step(self, step):
        self.ensure_one()
        if step in WIZARD_STEPS:
            self.wizard_step = step
        return True

    # ------------------------------------------------------------------
    # Flujo de aprobación
    # ------------------------------------------------------------------

    def action_submit(self):
        """Enviar a aprobación (antes «Guardar y Finalizar»)."""
        for record in self:
            if record.state != 'draft':
                raise UserError("Solo se pueden enviar requisiciones en Borrador.")
            for step in WIZARD_STEPS:
                record._check_step(step)

            record.write({
                'state': 'to_approve',
                # El folio se asigna al enviar, para que los borradores abandonados no dejen huecos
                'folio': record.folio or self.env['ir.sequence'].next_by_code('hr.requisition'),
                'submit_date': fields.Datetime.now(),
                'rejection_reason': False,
                'rejected_by_id': False,
            })
            first_approver = record._get_first_approver()
            if first_approver and first_approver == record.requestor_id:
                # El solicitante es el Director: su envío cuenta como la aprobación de Dirección
                record.write({
                    'state': 'first_approval',
                    'first_approver_id': first_approver.id,
                    'first_approval_date': fields.Datetime.now(),
                })
            approver = record._get_pending_approver()
            record._schedule_approval_activity(approver)
            if approver:
                record._notify(
                    Markup("Nueva requisición de personal de <b>%s</b>. Requiere tu aprobación.") % record.requestor_id.name,
                    approver.partner_id,
                )

        return {
            'effect': {
                'fadeout': 'slow',
                'message': '¡Requisición enviada a aprobación!',
                'type': 'rainbow_man',
            },
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self[:1].id,
            'views': [(False, 'form')],
            'target': 'current',
        }

    def action_approve(self):
        """1ª aprobación (Dirección)."""
        self._check_current_approver()
        for record in self:
            if record.state != 'to_approve':
                raise UserError("La requisición no está esperando la aprobación de Dirección.")
            record._close_approval_activities(f"Aprobada por {self.env.user.name}")
            record.write({
                'state': 'first_approval',
                'first_approver_id': self.env.user.id,
                'first_approval_date': fields.Datetime.now(),
            })
            final_approver = record._get_final_approver()
            record._schedule_approval_activity(final_approver)
            record._notify(
                Markup("<b>%s</b> aprobó la requisición. Pasa a aprobación final.") % self.env.user.name,
                final_approver.partner_id | record.requestor_id.partner_id,
            )
        return True

    def action_confirm_approve(self):
        """Aprobación final."""
        self._check_current_approver()
        for record in self:
            if record.state != 'first_approval':
                raise UserError("La requisición no está esperando la aprobación final.")
            record._close_approval_activities(f"Aprobada por {self.env.user.name}")
            record.write({
                'state': 'approved',
                'final_approver_id': self.env.user.id,
                'final_approval_date': fields.Datetime.now(),
            })
            record._notify(
                Markup("✅ Requisición <b>aprobada</b> por %s. Talento Humano ya puede aperturar la vacante.") % self.env.user.name,
                record.requestor_id.partner_id | record._get_director_employee().user_id.partner_id,
            )
        return True

    def action_reject(self):
        """Abre la ventana para capturar el motivo del rechazo."""
        self._check_current_approver()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Rechazar requisición',
            'res_model': 'hr.requisition.reject.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_requisition_id': self.id},
        }

    def _do_reject(self, reason):
        self._check_current_approver()
        for record in self:
            if record.state not in ('to_approve', 'first_approval'):
                raise UserError("Solo se pueden rechazar requisiciones en aprobación.")
            record._close_approval_activities(f"Rechazada por {self.env.user.name}")
            record.write({
                'state': 'rejected',
                'rejected_by_id': self.env.user.id,
                'rejection_reason': reason,
            })
            partners = record.requestor_id.partner_id
            if record.first_approver_id:
                partners |= record.first_approver_id.partner_id
            record._notify(
                Markup("❌ Requisición <b>rechazada</b> por %s.<br/>Motivo: %s") % (self.env.user.name, reason),
                partners,
            )
        return True

    def action_reset_to_draft(self):
        """Regresar a Borrador para corregir y volver a enviar."""
        is_recruitment_manager = self.env.user.has_group('hr_recruitment.group_hr_recruitment_manager')
        for record in self:
            if record.state not in ('approved', 'rejected'):
                raise UserError("Solo se pueden regresar a Borrador requisiciones aprobadas o rechazadas.")
            if record.state == 'approved' and not is_recruitment_manager:
                raise UserError("Solo Talento Humano puede regresar a Borrador una requisición aprobada.")
            if record.state == 'rejected' and not (record.requestor_id == self.env.user or is_recruitment_manager):
                raise UserError("Solo el solicitante o Talento Humano pueden corregir una requisición rechazada.")
            if record.is_published:
                record.action_close_vacancy(from_job=False)
            record.write({
                'state': 'draft',
                'wizard_step': 'especificaciones',
                'first_approver_id': False,
                'first_approval_date': False,
                'final_approver_id': False,
                'final_approval_date': False,
            })
        return True

    # ------------------------------------------------------------------
    # Publicación de la vacante
    # ------------------------------------------------------------------

    def action_publish_vacancy(self, from_job=False):
        self.ensure_one()

        if self.state != 'approved':
            if not from_job:  # Solo mostrar error si no viene del puesto
                raise UserError("Solo puedes publicar vacantes aprobadas")
            return

        if self.is_published:
            if not from_job:  # Solo mostrar error si no viene del puesto
                raise UserError("La vacante ya está publicada")
            return

        # Actualizar la requisición
        self.write({
            'is_published': True,
            'publish_date': fields.Datetime.now(),
            'close_date': False
        })

        # Actualizar el puesto SOLO si no viene del puesto
        if not from_job and self.workstation_job_id:
            # sudo: publicar el puesto en el sitio web exige permisos de editor del sitio;
            # los botones de la requisición ya están limitados a Reclutamiento
            self.workstation_job_id.sudo().with_context(skip_requisition_update=True).write({
                'is_published': True
            })

        # Mostrar notificación solo si es acción manual
        if not from_job:
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

    def action_close_vacancy(self, from_job=False):
        self.ensure_one()

        if not self.is_published:
            if not from_job:  # Solo mostrar error si no viene del puesto
                raise UserError("La vacante no está publicada")
            return

        # Actualizar la requisición
        self.write({
            'is_published': False,
            'close_date': fields.Datetime.now()
        })

        # Actualizar el puesto SOLO si no viene del puesto
        if not from_job and self.workstation_job_id:
            # sudo: publicar el puesto en el sitio web exige permisos de editor del sitio;
            # los botones de la requisición ya están limitados a Reclutamiento
            self.workstation_job_id.sudo().with_context(skip_requisition_update=True).write({
                'is_published': False
            })

        # Mostrar notificación solo si es acción manual
        if not from_job:
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


class HrRequisitionRejectWizard(models.TransientModel):
    _name = 'hr.requisition.reject.wizard'
    _description = 'Rechazar requisición de personal'

    requisition_id = fields.Many2one('hr.requisition', required=True)
    reason = fields.Text(string="Motivo del rechazo", required=True)

    def action_confirm(self):
        self.ensure_one()
        self.requisition_id._do_reject(self.reason)
        return {'type': 'ir.actions.act_window_close'}
