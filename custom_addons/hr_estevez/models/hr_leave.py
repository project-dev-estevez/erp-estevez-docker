from odoo import models, fields, api
from datetime import datetime, timedelta
import logging
import json
import requests

_logger = logging.getLogger(__name__)

class HrLeave(models.Model):
    _inherit = 'hr.leave'
    
    period_id = fields.Many2one('hr.vacation.period', string="Periodo de Vacaciones")

    def action_approve(self):
        """Sobrescribir la aprobación para asignar período automáticamente"""
        # Primero llamar al método original
        res = super().action_approve()
        
        for leave in self:
            # Comprobación más segura para evitar errores
            if (leave.holiday_status_id.is_vacation and 
                leave.employee_id and 
                leave.request_date_from):
                
                # Buscar el período correspondiente
                period = self.env['hr.vacation.period'].search([
                    ('employee_id', '=', leave.employee_id.id),
                    ('year_start', '<=', leave.request_date_from),
                    ('year_end', '>=', leave.request_date_from)
                ], limit=1)
                
                if period:
                    leave.period_id = period
                    # Forzar recomputación de días tomados
                    period._compute_days_taken()
        
        return res
    
    def _assign_period_to_leaves(self):
        """Asignar período a solicitudes de vacaciones existentes"""
        vacation_leaves = self.env['hr.leave'].search([
            ('holiday_status_id.is_vacation', '=', True),
            ('state', '=', 'validate'),
            ('period_id', '=', False)
        ])
        
        for leave in vacation_leaves:
            period = self.env['hr.vacation.period'].search([
                ('employee_id', '=', leave.employee_id.id),
                ('year_start', '<=', leave.request_date_from),
                ('year_end', '>=', leave.request_date_from)
            ], limit=1)
            
            if period:
                leave.period_id = period
        
        # Recalcular todos los períodos
        periods = self.env['hr.vacation.period'].search([])
        periods._compute_days_taken()
    
    def write(self, vals):
        """Actualizar días cuando cambia el estado"""
        res = super().write(vals)
        
        if 'state' in vals:
            for leave in self:
                if leave.period_id:
                    leave.period_id._compute_days_taken()
        
        return res

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for record in records:
            if (record.holiday_status_id.is_vacation and 
                record.employee_id and 
                record.request_date_from):
                
                period = self.env['hr.vacation.period'].search([
                    ('employee_id', '=', record.employee_id.id),
                    ('year_start', '<=', record.request_date_from),
                    ('year_end', '>=', record.request_date_from)
                ], limit=1)
                
                if period:
                    record.period_id = period
        return records
    
    def _assign_period_to_existing_leaves(self):
        """Asignar período a solicitudes de vacaciones existentes"""
        vacation_leaves = self.env['hr.leave'].search([
            ('holiday_status_id.is_vacation', '=', True),
            ('state', '=', 'validate'),
            ('period_id', '=', False)
        ])
        
        for leave in vacation_leaves:
            period = self.env['hr.vacation.period'].search([
                ('employee_id', '=', leave.employee_id.id),
                ('year_start', '<=', leave.request_date_from),
                ('year_end', '>=', leave.request_date_from)
            ], limit=1)
            
            if period:
                leave.period_id = period
        
        # Recalcular todos los períodos
        periods = self.env['hr.vacation.period'].search([])
        periods._compute_days_taken()

    def unlink(self):
        period_ids = self.mapped('period_id')
        res = super().unlink()
        for period in period_ids:
            # Forzar recomputación después de eliminar
            period._compute_days_taken()
        return res