from odoo import models, fields, api
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

class HrVacationPeriod(models.Model):
    _name = 'hr.vacation.period'
    _description = 'Periodo de Vacaciones'
    _order = 'year_start asc'
    
    display_name = fields.Char(compute='_compute_display_name', store=True)
    employee_id = fields.Many2one('hr.employee', required=True, ondelete='cascade')
    period = fields.Char(string="Periodo", compute='_compute_period', store=True)
    year_start = fields.Date(string="Inicio", required=True)
    year_end = fields.Date(string="Fin", required=True)
    entitled_days = fields.Float(string="Días Derecho")
    days_taken = fields.Float(string="Días Tomados", compute='_compute_days_taken', store=True)
    days_remaining = fields.Float(string="Días Restantes", compute='_compute_days_remaining', store=True)
    leave_ids = fields.One2many('hr.leave', 'period_id')
    allocation_ids = fields.One2many('hr.vacation.allocation', 'period_id', string="Asignaciones")

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

    @api.depends('leave_ids', 'leave_ids.state', 'leave_ids.number_of_days', 'allocation_ids', 'allocation_ids.days')
    def _compute_days_taken(self):
        _logger.info("=== CALCULANDO DÍAS TOMADOS ===")
        for period in self:
            _logger.info(f"Calculando período: {period.display_name}")
            
            # Días de solicitudes directas aprobadas
            direct_days = sum(period.leave_ids.filtered(
                lambda l: l.state == 'validate'
            ).mapped('number_of_days'))
            
            # Días de asignaciones aprobadas
            allocation_days = sum(period.allocation_ids.filtered(
                lambda a: a.leave_id.state == 'validate'
            ).mapped('days'))
            
            period.days_taken = direct_days + allocation_days
            _logger.info(f"Período {period.id}: Días directos: {direct_days}, Días de asignaciones: {allocation_days}, Total: {period.days_taken}")

    @api.depends('entitled_days', 'days_taken')
    def _compute_days_remaining(self):
        _logger.info("=== CALCULANDO DÍAS RESTANTES ===")
        for record in self:
            record.days_remaining = record.entitled_days - record.days_taken
            _logger.info(f"Período {record.id}: Días derecho: {record.entitled_days}, Días tomados: {record.days_taken}, Días restantes: {record.days_remaining}")