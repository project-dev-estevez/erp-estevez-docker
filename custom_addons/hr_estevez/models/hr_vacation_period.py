from odoo import models, fields, api
from odoo.exceptions import UserError

class HrVacationPeriod(models.Model):
    _name = 'hr.vacation.period'
    _description = 'Periodo de Vacaciones'
    
    # Añade este campo para mostrar en tags
    display_name = fields.Char(compute='_compute_display_name', store=True)
    
    employee_id = fields.Many2one('hr.employee', required=True, ondelete='cascade')
    period = fields.Char(string="Periodo", compute='_compute_period', store=True)
    year_start = fields.Date(string="Inicio", required=True)
    year_end = fields.Date(string="Fin", required=True)
    entitled_days = fields.Float(string="Días Derecho")
    days_taken = fields.Float(string="Días Tomados", compute='_compute_days_taken', store=True)
    days_remaining = fields.Float(string="Días Restantes", compute='_compute_days_remaining', store=True)
    leave_ids = fields.One2many('hr.leave', 'period_id')

    @api.depends('period', 'entitled_days', 'days_remaining')
    def _compute_display_name(self):
        for record in self:
            record.display_name = (
                f"{record.period}: {record.entitled_days}d derecho, "
                f"{record.days_taken}d usados, {record.days_remaining}d restantes"
            )

    @api.depends('year_start', 'year_end')
    def _compute_period(self):
        for record in self:
            if record.year_start and record.year_end:
                record.period = f"{record.year_start.year}-{record.year_end.year}"
            else:
                record.period = False

    # Usa number_of_days en lugar de number_of_days_display
    @api.depends('leave_ids', 'leave_ids.state', 'leave_ids.number_of_days')
    def _compute_days_taken(self):
        for period in self:
            # Filtrar solo las solicitudes aprobadas
            valid_leaves = period.leave_ids.filtered(
                lambda l: l.state == 'validate'
            )
            # Sumar los días de las solicitudes aprobadas
            period.days_taken = sum(valid_leaves.mapped('number_of_days'))

    @api.depends('entitled_days', 'days_taken')
    def _compute_days_remaining(self):
        for record in self:
            record.days_remaining = record.entitled_days - record.days_taken
