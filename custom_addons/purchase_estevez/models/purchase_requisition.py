import logging
from odoo import models, fields, api, exceptions
from odoo.exceptions import ValidationError
from datetime import date

_logger = logging.getLogger(__name__)

class PurchaseRequisition(models.Model):
    _name = 'purchase.requisition'
    _description = 'Requisition'

    state = fields.Selection([
        ('to_approve', 'Por Aprobar'),
        ('first_approval', 'En Curso'),
        ('rejected', 'Rechazado'),
        ('approved', 'Aprobado'),
    ], string="Estado", default='to_approve')

    # Información del solicitante
    requestor_id = fields.Many2one('res.users', string="Solicitante", default=lambda self: self.env.user, required=True, readonly=True)
    company_id = fields.Many2one('res.company', string="Empresa", related='requestor_id.company_id', readonly=True, store=False)
    direction_id = fields.Many2one('hr.direction', string="Dirección", related='requestor_id.employee_id.direction_id', readonly=True, store=False)
    department_id = fields.Many2one('hr.department', string="Departamento", related='requestor_id.employee_id.department_id', readonly=True, store=False)
    job_id = fields.Many2one('hr.job', string="Puesto Solicitante", related='requestor_id.employee_id.job_id', readonly=True, store=False)

    state_id = fields.Many2one(
        'res.country.state',
        string='Mercado',
        domain="[('country_id.code', '=', 'MX')]"
    )

    project_id = fields.Char(string='Proyecto')
    segment = fields.Char(string='Segmento')

    request_type = fields.Selection([
        ('camp', 'Campamento'),
        ('lodging', 'Hospedaje'),
        ('store', 'Almacén'),
        ('machinery_equipment', 'Maquinaría y equpo'),
        ('service_payment', 'Pago de servicio'),
        ('freight', 'Flete'),
    ], string='Tipo de Solicitud')

    date_start = fields.Date(string="Fecha de inicio")
    date_end = fields.Date(string="Fecha de finalización")
    duration_days = fields.Char(
        string="Días y noches",
        compute="_compute_duration_days",
        store=True,
        help="Días calculados entre fecha inicio y fin"
    )


    priority = fields.Selection([
        ('urgent', 'Urgente'),
        ('recurrent', 'Recurrente'),
        ('scheduled', 'Programada'),
    ], string='Nivel Prioridad')

    activity_to_do = fields.Text(
        string="¿Qué actividad se realizará?",
        help="Descripción de la actividad"
    )
    why_is_activity_to_do = fields.Text(
        string="¿Por qué se realizará la actividad?",
        help="Explicación de la razón de la actividad"
    )
    what_is_activity_to_do = fields.Text(
        string="¿Para que se realiza la actividad",
        help="Explicación de la función de la actividad"
    )
    comments = fields.Text(
        string="Comentarios",
        help="Comentarios adicionales para el solicitante"
    )

    #Campos de campamento
    vehicle_count = fields.Integer(
        string="Número de vehículos",
        default=1,  # Valor predeterminado
        help="Cantidad total de vehículos requeridos",
        # Restricciones opcionales:
        required=True,  # Obligatorio
        positive=True,  # Solo números positivos
    )

    type_vehicle = fields.Selection([
        ('NP-300', 'NP-300'),
        ('RAM', 'RAM'),
        ('utilitarian', 'Utilitario'),
    ], string='Tipo Vehiculo')

    number_rooms = fields.Integer(
        string="Número de habitaciones",
        default=1,  # Valor predeterminado
        help="Cantidad total de habitaciones requeridos",
        # Restricciones opcionales:
        required=True,  # Obligatorio
        positive=True,  # Solo números positivos
    )

    number_beds = fields.Integer(
        string="Número de camas",
        default=1,  # Valor predeterminado
        help="Cantidad total de camas requeridos",
        # Restricciones opcionales:
        required=True,  # Obligatorio
        positive=True,  # Solo números positivos
    )

    service_ids = fields.Many2many('purchase.requisition.service', string="Servicios")
    employee_id = fields.Many2one('hr.employee', string="Persona responsable")

    responsible_number = fields.Integer(
        string="Número del responsable",
        default=1,  # Valor predeterminado
        help="Numero requerido",
        # Restricciones opcionales:
        required=True,  # Obligatorio
        positive=True,  # Solo números positivos
    )

    employee_ids = fields.Many2many('hr.employee', string="Listado de personal")

    fiscal_situation = fields.Binary(string="Subir archivo")
    fiscal_situation_name = fields.Char(string="Nombre del archivo")

    letter_responsibility = fields.Binary(string="Subir archivo")
    letter_responsibility_name = fields.Char(string="Nombre del archivo")

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

    @api.constrains('date_start', 'date_end')
    def _check_dates(self):
        for record in self:
            if record.date_start and record.date_end:
                if record.date_start > record.date_end:
                    raise exceptions.ValidationError(
                        "⚠️ La fecha de inicio no puede ser posterior a la fecha final."
                    )
    @api.depends('date_start', 'date_end')
    def _compute_duration_days(self):
        for record in self:
            if record.date_start and record.date_end:
                start = fields.Date.from_string(record.date_start)
                end = fields.Date.from_string(record.date_end)
                delta = end - start
                days = delta.days
                nights = max(days - 1, 0)  # Evita números negativos
                record.duration_days = f"{days} días y {nights} noches"
            else:
                record.duration_days = "0 días y 0 noches"