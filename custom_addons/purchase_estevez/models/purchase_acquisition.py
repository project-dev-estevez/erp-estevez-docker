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
    acquisition_id = fields.Many2one('purchase.acquisition', string='Acquisition') 
    order_line_ids = fields.One2many('purchase.acquisition.line', 'acquisition_id', string='Order Lines')      
    proveedor_id = fields.Many2one('res.partner', string="Proveedor", required=True, domain="[('supplier_rank', '>', 0)]")
    fecha_limite_entrega = fields.Date(string='Fecha límite de entrega', required=True)    
    tipo = fields.Char(string='Tipo', required=True, default='Producto')
    proyecto = fields.Char(string='Proyecto', required=True)
    segmento = fields.Char(string='Segmento', required=True)
    product_id = fields.Many2one('product.product', string='Product', required=True)
    product_qty = fields.Float(string='Quantity', required=True, default=1.0)
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
    requisition_number = fields.Char(string="Número de requisición")

    state = fields.Selection([
        ('to_approve', 'Pendiente Aprobación'),
        ('first_approval', 'En Curso'),
        ('rejected', 'Rechazado'),
        ('approved', 'Aprobado'),
    ], string="Estado", default='to_approve')    

    def action_purchase(self):
        self.ensure_one()
        order_lines = []
        for line in self.order_line_ids:
            order_lines.append((0, 0, {
                'product_id': line.product_id.id,  
                'product_qty': line.product_qty,  
                'product_uom': line.product_uom.id,  
                'price_unit': line.price_unit,    
            }))

        purchase_order = self.env['purchase.order'].create({
            'partner_id': self.proveedor_id.id,  
            'origin': self.requisition_number,   
            'order_line': order_lines,           
        })
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.order',
            'res_id': purchase_order.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_quotation(self):
        self.ensure_one()                            
        order_lines = []
        for line in self.order_line_ids:
            order_lines.append((0, 0, {
                'product_id': line.product_id.id,
                'product_qty': line.product_qty,
                'product_uom': line.product_uom.id,
                'price_unit': line.price_unit,
            }))
        
        quotation = self.env['purchase.order'].create({
            'partner_id': self.requestor_id.partner_id.id,
            'origin': self.requisition_number,
            'order_line': order_lines,
        })    
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Cotización',
            'res_model': 'purchase.order',
            'res_id': quotation.id,
            'view_mode': 'form',  
            'target': 'current', 
        }  

    def action_approve(self):
        self.state = 'first_approval'
        
        if not self.direction_id:
            _logger.warning("No se encontro director para la adquisición")
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
            "type": "ir.actions.act_window_close",
        }
    
