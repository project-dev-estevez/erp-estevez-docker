from odoo import models, fields, api
from datetime import datetime, timedelta
import logging
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class HrLeave(models.Model):
    _inherit = 'hr.leave'
    
    period_id = fields.Many2one('hr.vacation.period', string="Periodo de Vacaciones")
    allocation_ids = fields.One2many('hr.vacation.allocation', 'leave_id', string="Distribución por Períodos")

    def _distribute_vacation_days(self):
        """Distribuye los días de vacaciones entre los períodos disponibles"""
        HrVacationAllocation = self.env['hr.vacation.allocation']
        
        for leave in self:
            if not (leave.holiday_status_id.is_vacation and 
                   leave.employee_id and 
                   leave.number_of_days > 0):
                continue
                
            # Eliminar asignaciones existentes para esta solicitud
            leave.allocation_ids.unlink()
            
            # Obtener períodos ordenados por antigüedad (más antiguo primero)
            periods = self.env['hr.vacation.period'].search([
                ('employee_id', '=', leave.employee_id.id)
            ], order='year_start asc')
            
            days_remaining = leave.number_of_days
            allocation_vals = []
            
            for period in periods:
                if days_remaining <= 0:
                    break
                    
                # Calcular días disponibles en este período
                available_days = period.days_remaining
                
                if available_days <= 0:
                    continue
                
                # Calcular cuántos días tomar de este período
                days_to_take = min(days_remaining, available_days)
                
                if days_to_take > 0:
                    allocation_vals.append({
                        'leave_id': leave.id,
                        'period_id': period.id,
                        'days': days_to_take,
                    })
                    days_remaining -= days_to_take
            
            if days_remaining > 0:
                raise UserError(f"No hay suficientes días disponibles. Faltan {days_remaining} días.")
            
            # Crear las asignaciones
            if allocation_vals:
                HrVacationAllocation.create(allocation_vals)

    def action_approve(self):
        """Sobrescribir la aprobación para distribuir días automáticamente"""
        # Primero distribuir los días
        vacation_leaves = self.filtered(
            lambda l: l.holiday_status_id.is_vacation and 
                     l.employee_id and 
                     l.number_of_days > 0
        )
        
        for leave in vacation_leaves:
            leave._distribute_vacation_days()
        
        # Luego llamar al método original
        res = super().action_approve()
        
        # Forzar recálculo de días en los períodos afectados
        periods_to_update = vacation_leaves.mapped('allocation_ids.period_id')
        if periods_to_update:
            periods_to_update._compute_days_taken()
            periods_to_update._compute_days_remaining()
        
        return res

    def write(self, vals):
        """Manejar cambios de estado"""
        res = super().write(vals)
        
        if 'state' in vals:
            # Recalcular días en períodos afectados cuando cambia el estado
            for leave in self:
                if leave.allocation_ids:
                    periods = leave.allocation_ids.mapped('period_id')
                    periods._compute_days_taken()
                    periods._compute_days_remaining()
        
        return res

    def unlink(self):
        """Manejar eliminación"""
        periods_to_update = self.mapped('allocation_ids.period_id')
        res = super().unlink()
        
        # Recalcular períodos afectados
        if periods_to_update:
            periods_to_update._compute_days_taken()
            periods_to_update._compute_days_remaining()
        
        return res