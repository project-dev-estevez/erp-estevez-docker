import logging
from odoo import models, fields, api, exceptions
from odoo.exceptions import ValidationError
from datetime import date
from dateutil.relativedelta import relativedelta

_logger = logging.getLogger(__name__)

class CustomDevolucion(models.Model):
    _inherit = 'mail.thread'
    _name = 'custom.devolucion'
    _description = 'Devoluciones'

    state = fields.Selection([
        ('borrador', 'Borrador'),
        ('aprobado', 'Aprobado'),
        ('cancelado', 'Cancelado'),
    ], default='borrador')

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
    
    """def _notify_approval(self, next_stage):
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
            }) """

# Acciones de estado
    def action_approve(self):
        self.state = 'aprobado'                
                

    def _notify_approval(self):
        """Enviar notificación de aprobación"""
        template = self.env.ref('stock_estevez.email_template_requisition_approved')
        template.send_mail(self.id, force_send=True)

    def action_reject(self):
        self.state = 'cancelado'
           

    def action_save(self):
        # Aquí puedes agregar cualquier lógica adicional antes de guardar
        self.ensure_one()
        self.write({'state': self.state})  # Esto guarda el registro
        _logger.info("Requisición guardada con éxito")
        return True