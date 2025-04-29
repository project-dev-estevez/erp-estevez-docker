import logging
from odoo import models, fields, api, exceptions
from odoo.exceptions import ValidationError
from datetime import date
from dateutil.relativedelta import relativedelta

_logger = logging.getLogger(__name__)

class StockRequisition(models.Model):
    _name = 'stock.requisition'
    _description = 'Stock Requisition'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    state = fields.Selection([
        ('draft', 'Borrador'),
        ('to_approve_ops', 'Por Aprobar (Operaciones)'),
        ('to_approve_pm', 'Por Aprobar (PM)'),
        ('to_approve_site_admin', 'Por Aprobar (Administración de Obra)'),
        ('to_approve_warehouse', 'Por Aprobar (Almacén)'),
        ('done', 'Entregado'),
        ('rejected', 'Rechazado')
    ], string="Estado", default='draft', tracking=True)

    # Información del solicitante
    requestor_id = fields.Many2one('res.users', string="Solicitante", default=lambda self: self.env.user, required=True, readonly=True)
    company_id = fields.Many2one('res.company', string="Empresa", related='requestor_id.company_id', readonly=True, store=False)
    department_id = fields.Many2one('hr.department', string="Departamento", related='requestor_id.employee_id.department_id', readonly=True, store=False)
    job_id = fields.Many2one('hr.job', string="Puesto Solicitante", related='requestor_id.employee_id.job_id', readonly=True, store=False)
    order_line_ids = fields.One2many('stock.requisition.line', 'requisition_id', string='Order Lines')

    name = fields.Char(
        string="Folio",
        required=True,
        readonly=True,
        default=lambda self: self.env['ir.sequence'].next_by_code('stock.requisition'),
        tracking=True
    )

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

    # Campos de aprobación
    ops_approver_id = fields.Many2one('res.users', string="Aprobado por Operaciones")
    pm_approver_id = fields.Many2one('res.users', string="Aprobado por PM")
    site_admin_approver_id = fields.Many2one('res.users', string="Aprobador Admin. Obra")
    warehouse_approver_id = fields.Many2one('res.users', string="Aprobado por Almacén")

    # Fechas de aprobación
    ops_approval_date = fields.Datetime()
    pm_approval_date = fields.Datetime()
    site_admin_approval_date = fields.Datetime()
    warehouse_approval_date = fields.Datetime()

    warehouse_location_id = fields.Many2one(
        'stock.location',
        string="Ubicación de Almacén",
        domain="[('usage', '=', 'internal')]",
        required=False,
        help="Seleccione la ubicación de almacén de donde se restará el material."
    )

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

    picking_id = fields.Many2one('stock.picking', string="Transferencia de Inventario")
    location_id = fields.Many2one(
        'stock.location',
        string="Ubicación de Origen",
        required=True,
        default=lambda self: self.env.ref('stock.stock_location_stock')
    )
    location_dest_id = fields.Many2one(
        'stock.location',
        string="Ubicación de Destino",
        required=True,
        default=lambda self: self.env.ref('stock.stock_location_customers')
    )
    assignment_ids = fields.One2many(
        'stock.assignment',
        'requisition_id',
        string="Asignaciones"
    )

    def action_done(self):
        self.write({'state': 'done'})

    @api.depends('personal_type', 'employee_id', 'personal_contract_id')
    def _compute_display_receiver(self):
        for rec in self:
            if rec.personal_type == 'internal':
                rec.display_receiver = rec.employee_id.name or ''
            else:
                rec.display_receiver = rec.personal_contract_id.name or ''

    def action_submit_ops(self):
        self.write({
            'state': 'to_approve_pm',
            'ops_approver_id': self.env.user.id,
            'ops_approval_date': fields.Datetime.now()
        })
        self.message_post(
            body=f"La solicitud {self.name} requiere aprobación del PM.",
            partner_ids=self.env.ref('stock_estevez.group_pm_approver').users.partner_id.ids
        )


    def action_approve_pm(self):
        self.write({
            'state': 'to_approve_site_admin',
            'pm_approver_id': self.env.user.id,
            'pm_approval_date': fields.Datetime.now()
        })
        self.message_post(
            body=f"La solicitud {self.name} requiere aprobación de AO.",
            partner_ids=self.env.ref('stock_estevez.group_site_admin_approver').users.partner_id.ids
        )

    def action_approve_site_admin(self):
        self.write({
            'state': 'to_approve_warehouse',
            'site_admin_approver_id': self.env.user.id,
            'site_admin_approval_date': fields.Datetime.now()
        })
        self.message_post(
            body=f"La solicitud {self.name} requiere aprobación de Almacen.",
            partner_ids=self.env.ref('stock_estevez.group_warehouse').users.partner_id.ids
        )

    def action_approve_warehouse(self):
        self.write({
            'state': 'done',
            'warehouse_approver_id': self.env.user.id,
            'warehouse_approval_date': fields.Datetime.now()
        })

    def action_reject(self):
        self.write({'state': 'rejected'})

    def _get_approvers(self, department):
        # Ejemplo: Obtener el jefe del departamento
        return self.env['hr.employee'].search([
            ('department_id.name', 'ilike', department),
            ('parent_id', '=', False)  # Suponiendo que el jefe no tiene supervisor
        ]).user_id
    
    def _notify_approval(self, next_stage):
        template = False
        recipients = []
        
        if next_stage == 'pm':
            template = self.env.ref('stock_estevez.email_template_approval_pm')
            recipients = self._get_approvers('Project Management')
        elif next_stage == 'admin':
            template = self.env.ref('stock_estevez.email_template_approval_admin')
            recipients = self._get_approvers('Administración de Obra')
        elif next_stage == 'warehouse':
            template = self.env.ref('stock_estevez.email_template_approval_warehouse')
            recipients = self._get_approvers('Almacén')

        if template and recipients:
            template.send_mail(self.id, email_values={
                'email_to': ','.join(recipients.mapped('email'))
            })

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
        self_sudo = self.sudo()
        
        if self_sudo.state != 'to_approve_warehouse':
            raise exceptions.UserError("Solo se puede confirmar aprobación desde el estado 'Por Aprobar Almacen'")
        
        # Validar campos requeridos
        required_fields = [
            (self_sudo.warehouse_location_id, "Debe seleccionar una ubicación de almacén"),
            (self_sudo.location_dest_id, "Debe configurar la ubicación destino"),
            (self_sudo.order_line_ids, "La requisición no tiene productos asignados")
        ]
        
        for field, error_msg in required_fields:
            if not field:
                raise exceptions.UserError(error_msg)
        
        # ================== VALIDACIONES DE STOCK ==================
        # 1. Validar stock físico en la ubicación seleccionada
        for line in self_sudo.order_line_ids:
            if line.product_id.type != 'product':
                continue  # Solo validar productos almacenables
                
            qty_available = self_sudo.env['stock.quant']._get_available_quantity(
                line.product_id,
                self_sudo.warehouse_location_id
            )
            
            if qty_available < line.product_qty:
                raise exceptions.UserError(
                    f"Stock insuficiente en {self_sudo.warehouse_location_id.complete_name}\n"
                    f"Producto: {line.product_id.name}\n"
                    f"Disponible: {qty_available} | Requerido: {line.product_qty}"
                )
        
        # ================== CREACIÓN DE TRANSFERENCIA ==================
        picking_type = self_sudo.env.ref('stock.picking_type_out')
        
        picking_vals = {
            'picking_type_id': picking_type.id,
            'location_id': self_sudo.warehouse_location_id.id,
            'location_dest_id': self_sudo.location_dest_id.id,
            'origin': self_sudo.name,
            'partner_id': self_sudo._get_recipient_partner().id,
            'scheduled_date': fields.Datetime.now(),
        }
        
        picking = self_sudo.env['stock.picking'].create(picking_vals)
        
        # Crear movimientos con la ubicación correcta
        moves = self_sudo.env['stock.move']
        for line in self_sudo.order_line_ids:
            move_vals = {
                'name': line.product_id.name,
                'product_id': line.product_id.id,
                'product_uom_qty': line.product_qty,
                'location_id': self_sudo.warehouse_location_id.id,
                'location_dest_id': self_sudo.location_dest_id.id,
                'picking_id': picking.id,
                'state': 'draft',
            }
            moves += self_sudo.env['stock.move'].create(move_vals)
        
        # ================== VALIDACIÓN AUTOMÁTICA ==================
        picking.action_confirm()
        picking.action_assign()
        
        # 2. Validar reserva completa
        unavailable_moves = picking.move_ids.filtered(
            lambda m: sum(m.move_line_ids.mapped('quantity')) < m.product_uom_qty
        )
        
        if unavailable_moves:
            products = "\n- ".join([m.product_id.name for m in unavailable_moves])
            raise exceptions.UserError(
                f"Productos no reservados completamente:\n- {products}"
            )
        
        # Marcar cantidad realizada = reservada
        for move_line in picking.move_line_ids:
            move_line.quantity = move_line.quantity
        
        picking.button_validate()
        
        # ================== ACTUALIZACIÓN DE REGISTRO ==================
        assignment_lines = []
        recipient = self_sudo._get_recipient()

        for move in picking.move_ids:
            # Sumar las cantidades realizadas de las líneas de movimiento
            total_done = sum(move.move_line_ids.mapped('quantity'))
            
            assignment_vals = {
                'product_id': move.product_id.id,
                'quantity': total_done,
                'recipient_id': recipient.id,
                'assignment_date': fields.Datetime.now(),
                'stock_move_id': move.id,
            }
            assignment_lines.append((0, 0, assignment_vals))
        
        self_sudo.write({
            'state': 'done',
            'picking_id': picking.id,
            'assignment_ids': assignment_lines,
            'warehouse_approver_id': self_sudo.env.user.id,
            'warehouse_approval_date': fields.Datetime.now()
        })
        
        # ================== NOTIFICACIONES ==================
        self_sudo.message_post(
            body=f"""
            <div class="alert alert-success">
                <h4>Transferencia {picking.name} completada</h4>
                <p>Desde: {self_sudo.warehouse_location_id.complete_name}</p>
                <p>Hacia: {self_sudo.location_dest_id.complete_name}</p>
            </div>
            """
        )
        self_sudo._notify_approval()
        
        return True

    def _get_recipient(self):
        """Obtener el receptor según el tipo de personal"""
        if self.personal_type == 'internal':
            if not self.employee_id:
                raise exceptions.UserError("Debe seleccionar un empleado receptor")
            return self.employee_id
        else:
            if not self.personal_contract_id:
                raise exceptions.UserError("Debe seleccionar un contratista receptor")
            return self.personal_contract_id

    def _get_recipient_partner(self):
        """Obtener partner asociado al receptor"""
        recipient = self._get_recipient()
        if recipient.user_id.partner_id:
            return recipient.user_id.partner_id
        raise exceptions.UserError(f"El receptor {recipient.name} no tiene usuario asociado")

    def _notify_approval(self):
        """Enviar notificación de aprobación"""
        template = self.env.ref('stock_estevez.email_template_requisition_approved')
        template.send_mail(self.id, force_send=True)

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

    def action_validate_delivery(self):
        self.ensure_one()
        if not self.picking_id:
            raise UserError("No hay transferencia asociada")
            
        if self.picking_id.state != 'assigned':
            raise UserError("Los productos no están disponibles")
            
        # Crear paquete de entrega
        package = self.env['stock.quant.package'].create({
            'name': f"PAQ-{self.name}",
        })
        
        # Procesar cada movimiento
        for move in self.picking_id.move_ids:
            move.move_line_ids.write({
                'qty_done': move.product_uom_qty,
                'result_package_id': package.id
            })
        
        # Validar la transferencia
        self.picking_id.button_validate()
        
        # Actualizar estado
        self.write({'state': 'done'})
        
        # Registrar en el chatter
        message = f"""
        <p>Materiales entregados correctamente:</p>
        <ul>
            <li>Paquete: {package.name}</li>
            <li>Receptor: {self.display_receiver}</li>
            <li>Ubicación destino: {self.location_dest_id.complete_name}</li>
        </ul>
        """
        self.message_post(body=message)

    def action_save(self):
        # Aquí puedes agregar cualquier lógica adicional antes de guardar
        self.ensure_one()
        self.write({'state': self.state})  # Esto guarda el registro
        _logger.info("Requisición guardada con éxito")
        return True