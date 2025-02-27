import logging
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import datetime

_logger = logging.getLogger(__name__)

class PurchaseAcquisition(models.Model):
    _name = 'purchase.acquisition'
    _description = 'Acquisition'

    # Información del solicitante
    requestor_id = fields.Many2one('res.users', string="Solicitante", default=lambda self: self.env.user, required=True, readonly=True)
    company_id = fields.Many2one('res.company', string="Empresa", related='requestor_id.company_id', readonly=True, store=False)
    direction_id = fields.Many2one('hr.direction', string="Dirección", related='requestor_id.employee_id.direction_id', readonly=True, store=False)
    department_id = fields.Many2one('hr.department', string="Departamento", related='requestor_id.employee_id.department_id', readonly=True, store=False)
    job_id = fields.Many2one('hr.job', string="Puesto Solicitante", related='requestor_id.employee_id.job_id', readonly=True, store=False)

    medida = fields.Selection(
        selection=[            
            ('pieza', 'Pieza'),
            ('juego', 'Juego'),
            ('kilogramo', 'Kilogramo'),
            ('litro', 'Litro'),
            ('metro', 'Metro'),
            ('otro', 'Otro'),
            ('caja', 'Caja'),
            ('centimetro', 'Centimetro'),
            ('horas', 'Horas'),
            ('kit', 'Kit'),
            ('kilometro', 'Kilometro'),
            ('lote', 'Lote'),
            ('metro_cuadrado','Metro cuadrado'),
            ('metro_cubico', 'Metro cubico'),
            ('metro_lineal', 'Metro lineal'),
            ('rollo', 'Rollo'),
            ('servicio', 'Servicio'),
            ('tonelada', 'Tonelada'),
            ('bolsa', 'Bolsa'),
            ('cubeta', 'Cubeta'),
            ('paquete', 'Paquete'),
            ('galon', 'Galon'),
            ('bidon', 'Bidon'),
            ('pares', 'Pares'),
            ('no_aplica', 'No aplica'),
        ],
        string='Unidad', required=True)

    #Adquisiciones

    fecha_limite_entrega = fields.Date(string='Fecha límite de entrega', required=True)    
    tipo = fields.Char(string='Tipo', required=True, default='Producto')
    proyecto = fields.Char(string='Proyecto', required=True)
    segmento = fields.Char(string='Segmento', required=True)
    prioridad = fields.Selection(
        selection=[            
            ('urgente', 'Urgente'),
            ('recurrente', 'Stock'),
            ('programado', 'Programado'),
        ],
        string='Prioridad', required=True)                   
    almacen = fields.Char(string='Almacen', required=True)
    sugerencia = fields.Char(string='Sugerencia de proveedor', required=True)
    comentarios = fields.Char(string='Comentarios', required=True)
    nombre_producto = fields.Many2one('product.product', string='Nombre del producto', required=True)
    cantidad = fields.Integer(string='Cantidad', required=True)    
    descripcion = fields.Char(string='Descripcion', required=True)
    especificaciones = fields.Char(string='Especificaciones', required=True)

    state = fields.Selection([
        ('to_approve', 'Pendiente Aprobación'),
        ('first_approval', 'En Curso'),
        ('rejected', 'Rechazado'),
        ('approved', 'Aprobado'),
    ], string="Estado", default='to_approve')

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

    @api.constrains('cantidad')
    def _check_cantidad(self):
        for record in self:
            if record.cantidad < 0:
                raise ValidationError("La cantidad debe ser mayor que cero")

    @api.constrains('fecha_limite_entrega')
    def _check_fecha_limite_entrega(self):
        for record in self:
            if record.fecha_limite_entrega and record.fecha_limite_entrega < fields.Date.today():
                raise ValidationError("La fecha límite de entrega debe ser posterior a la fecha actual")

    def save_dat(self):
        #Metodo para el bootn de Guardar
        self.ensure_one()
        return {
            "type": "ir.actions.act_window_close",  # Cierra la ventana de este formulario
        }

    

