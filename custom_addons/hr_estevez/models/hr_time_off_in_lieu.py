from odoo import models, fields, api
from odoo.exceptions import UserError

class HrTimeOffInLieu(models.Model):
    _name = 'hr.time.off.in.lieu'
    _description = 'Tiempo por Tiempo (TXT)'
    _order = 'request_date desc'
    
    name = fields.Char(string="Descripción", required=True)
    employee_id = fields.Many2one('hr.employee', string="Empleado", required=True, ondelete='cascade')
    request_date = fields.Date(string="Fecha de Solicitud", default=fields.Date.today, required=True)
    request_date_from = fields.Date(string="Fecha Inicio", required=True)
    request_date_to = fields.Date(string="Fecha Fin", required=True)
    number_of_days = fields.Float(string="Días Solicitados", compute='_compute_number_of_days', store=True)
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('pending', 'Pendiente'),
        ('approved', 'Aprobado'),
        ('rejected', 'Rechazado')
    ], string="Estado", default='draft', required=True)
    notes = fields.Text(string="Notas")
    
    # Campo relacionado con la ausencia creada
    leave_id = fields.Many2one('hr.leave', string="Ausencia Relacionada")
    
    @api.depends('request_date_from', 'request_date_to')
    def _compute_number_of_days(self):
        for record in self:
            if record.request_date_from and record.request_date_to:
                if record.request_date_to < record.request_date_from:
                    record.number_of_days = 0
                    raise UserError("La fecha fin no puede ser anterior a la fecha inicio")
                
                # Usar el método de Odoo para calcular días considerando días laborales
                date_from = fields.Date.from_string(record.request_date_from)
                date_to = fields.Date.from_string(record.request_date_to)
                
                # Calcular diferencia en días (simple)
                delta = date_to - date_from
                record.number_of_days = delta.days + 1  # +1 para incluir ambos días
            else:
                record.number_of_days = 0.0
    
    def action_submit(self):
        if self.state != 'draft':
            raise UserError("Solo se puede enviar una solicitud en estado Borrador")
        self.write({'state': 'pending'})
    
    def action_approve(self):
        if self.state != 'pending':
            raise UserError("Solo se puede aprobar una solicitud en estado Pendiente")
        for record in self:
            # Buscar el tipo de ausencia para TXT
            time_off_type = self.env['hr.leave.type'].search([
                ('is_time_off_in_lieu', '=', True)
            ], limit=1)
            
            if not time_off_type:
                raise UserError("No se encontró un tipo de ausencia configurado para Tiempo por Tiempo")
            
            # Crear la ausencia en Odoo
            leave_vals = {
                'name': record.name,
                'employee_id': record.employee_id.id,
                'holiday_status_id': time_off_type.id,
                'request_date_from': record.request_date_from,
                'request_date_to': record.request_date_to,
                'number_of_days_display': record.number_of_days,
                'state': 'confirm',
                'time_off_in_lieu_id': record.id,  # Relación inversa
            }
            
            leave = self.env['hr.leave'].create(leave_vals)
            record.leave_id = leave.id
            
            # Aprobar automáticamente la ausencia
            leave.action_approve()
            
        self.write({'state': 'approved'})
    
    def action_reject(self):
        if self.state != 'pending':
            raise UserError("Solo se puede rechazar una solicitud en estado Pendiente")
        # Si hay una ausencia relacionada, cancelarla
        for record in self:
            if record.leave_id:
                record.leave_id.action_refuse()
        self.write({'state': 'rejected'})
    
    def action_draft(self):
        if self.state not in ['approved', 'rejected']:
            raise UserError("Solo se puede volver a borrador desde estados Aprobado o Rechazado")
        # Si hay una ausencia relacionada, eliminarla
        for record in self:
            if record.leave_id:
                record.leave_id.unlink()
        self.write({'state': 'draft'})

    @api.model
    def create(self, vals):
        # Asegurar que el nombre se genere correctamente
        if not vals.get('name') or 'TXT' not in vals.get('name', ''):
            employee_id = vals.get('employee_id')
            if employee_id:
                employee = self.env['hr.employee'].browse(employee_id)
                date_from = vals.get('request_date_from', fields.Date.today())
                vals['name'] = f"TXT - {employee.name} - {date_from}"
        
        record = super().create(vals)
        return record