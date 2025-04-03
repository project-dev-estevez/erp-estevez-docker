from odoo import models, fields, api

class HrVacationPeriod(models.Model):
    _name = 'hr.vacation.period'
    _description = 'Periodo de Vacaciones'

    employee_id = fields.Many2one('hr.employee', string="Empleado", required=True, ondelete='cascade')
    year_start = fields.Date(string="Inicio del Periodo", required=True)
    year_end = fields.Date(string="Fin del Periodo", required=True)
    entitled_days = fields.Float(string="Días con Derecho", required=True)
    days_taken = fields.Float(string="Días Disfrutados", required=True)
    days_remaining = fields.Float(string="Días Restantes", compute="_compute_days_remaining", store=True)
    period = fields.Char(string="Periodo", compute="_compute_period", store=False)

    @api.depends('year_start', 'year_end')
    def _compute_period(self):
        for record in self:
            if record.year_start and record.year_end:
                record.period = f"{record.year_start.strftime('%Y')} - {record.year_end.strftime('%Y')}"

    @api.depends('entitled_days', 'days_taken')
    def _compute_days_remaining(self):
        for record in self:
            record.days_remaining = record.entitled_days - record.days_taken