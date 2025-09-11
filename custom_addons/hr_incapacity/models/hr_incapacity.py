from odoo import models, fields, api
from datetime import datetime


class HrIncapacity(models.Model):
    _name = 'hr.incapacity'
    _description = 'Incapacidades de Empleados'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char(string='Referencia', required=True, copy=False, readonly=True, default='Nuevo')
    employee_id = fields.Many2one('hr.employee', string='Empleado', required=True)
    department_id = fields.Many2one('hr.department', string='Departamento', related='employee_id.department_id', store=True)
    company_id = fields.Many2one('res.company', string='Compañía', related='employee_id.company_id', store=True)
    incapacity_type_id = fields.Many2one('hr.incapacity.type', string='Tipo de Incapacidad', required=True)
    incident_date = fields.Date(string='Fecha del Incidente', required=True, default=fields.Date.today)
    start_date = fields.Date(string='Fecha de Inicio', required=True)
    end_date = fields.Date(string='Fecha de Fin', required=True)
    days = fields.Integer(string='Días', compute='_compute_days', store=True)
    comments = fields.Text(string='Comentarios')
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('confirmed', 'Confirmada'),
        ('validated', 'Validada'),
        ('done', 'Realizada'),
        ('cancel', 'Cancelada')
    ], string='Estado', default='draft', tracking=True)

    @api.depends('start_date', 'end_date')
    def _compute_days(self):
        for record in self:
            if record.start_date and record.end_date:
                start = fields.Date.from_string(record.start_date)
                end = fields.Date.from_string(record.end_date)
                record.days = (end - start).days + 1
            else:
                record.days = 0

    @api.model
    def create(self, vals):
        if vals.get('name', 'Nuevo') == 'Nuevo':
            vals['name'] = self.env['ir.sequence'].next_by_code('hr.incapacity') or 'Nuevo'
        return super(HrIncapacity, self).create(vals)

    def action_confirm(self):
        self.write({'state': 'confirmed'})

    def action_validate(self):
        self.write({'state': 'validated'})

    def action_done(self):
        self.write({'state': 'done'})

    def action_cancel(self):
        self.write({'state': 'cancel'})

    def action_draft(self):
        self.write({'state': 'draft'})

    def action_view_incapacity(self):
        self.ensure_one()
        # Obtener la acción definida en XML
        action = self.env['ir.actions.act_window']._for_xml_id('hr_incapacity.action_hr_incapacity')
        # Añadir el dominio y contexto específicos
        action['domain'] = [('employee_id', '=', self.id)]
        action['context'] = {
            'default_employee_id': self.id,
            'search_default_employee_id': self.id
        }
        return action