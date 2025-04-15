import logging
from odoo import models, fields, api, exceptions
from odoo.exceptions import ValidationError
from datetime import date
from dateutil.relativedelta import relativedelta

_logger = logging.getLogger(__name__)

class StockRequisition(models.Model):
    _name = 'stock.requisition'
    _description = 'Stock Requisition'

    state = fields.Selection([
        ('to_approve', 'Por Aprobar'),
        ('first_approval', 'En Curso'),
        ('rejected', 'Rechazado'),
        ('approved', 'Aprobado'),
    ], string="Estado", default='to_approve')

    # Información del solicitante
    requestor_id = fields.Many2one('res.users', string="Solicitante", default=lambda self: self.env.user, required=True, readonly=True)
    company_id = fields.Many2one('res.company', string="Empresa", related='requestor_id.company_id', readonly=True, store=False)
    department_id = fields.Many2one('hr.department', string="Departamento", related='requestor_id.employee_id.department_id', readonly=True, store=False)
    job_id = fields.Many2one('hr.job', string="Puesto Solicitante", related='requestor_id.employee_id.job_id', readonly=True, store=False)
    order_line_ids = fields.One2many('stock.requisition.line', 'requisition_id', string='Order Lines') 

    state_id = fields.Many2one(
        'res.country.state',
        string='Estado',
        domain="[('country_id.code', '=', 'MX')]"
    )

    type_requisition = fields.Selection([
        ('general_warehouse', 'Almacén General'),
        ('ehs', 'Seguridad e Higiene'),
        ('kuali_digital', 'Kuali Digital'),
        ('high_cost', 'Alto Costo'),
        ('vehicle_control', 'Control Vehicular'),
        ('systems', 'Sistemas'),
        ('card', 'Tarjeta'),
        ('medical_area', 'Área Médica')

    ], string='Almacén de Origen')

    type_warehouse = fields.Selection([
        ('general_warehouse', 'Almacén General'),
        ('foreign_warehouse', 'Almacén Foraneo')
    ], string='Tipo Almacén')

    project_id = fields.Char(string='Proyecto')
    segment = fields.Char(string='Segmento')

    personal_type = fields.Selection([
        ('internal', 'Interno'),
        ('contractor', 'Contratista')
    ], string='Tipo de Persona que Recibe')

    employee_id = fields.Many2one('hr.employee', string="Persona que Recibe")

    supervisor_id = fields.Many2one('hr.employee', string="Supervisor")
    contractor_id = fields.Char(string='Contratista')
    personal_contract_id = fields.Many2one('hr.employee', string="Persona que Recibe")

    comments = fields.Text(
        string="Comentarios",
        help="Comentarios adicionales para el solicitante"
    )

    display_receiver = fields.Char(
        string="Recibe",
        compute='_compute_display_receiver',
        store=True
    )

    @api.depends('personal_type', 'employee_id', 'personal_contract_id')
    def _compute_display_receiver(self):
        for rec in self:
            if rec.personal_type == 'internal':
                rec.display_receiver = rec.employee_id.name or ''
            else:
                rec.display_receiver = rec.personal_contract_id.name or ''


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


    def action_save(self):
        # Aquí puedes agregar cualquier lógica adicional antes de guardar
        self.ensure_one()
        self.write({'state': self.state})  # Esto guarda el registro
        _logger.info("Requisición guardada con éxito")
        return True