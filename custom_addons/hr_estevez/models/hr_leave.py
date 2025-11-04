from odoo import models, fields, api
from datetime import datetime, timedelta
import logging
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class HrLeave(models.Model):
    _inherit = 'hr.leave'
    
    period_id = fields.Many2one('hr.vacation.period', string="Periodo de Vacaciones")
    allocation_ids = fields.One2many('hr.vacation.allocation', 'leave_id', string="Distribución por Períodos")

    time_off_in_lieu_id = fields.Many2one('hr.time.off.in.lieu', string="Solicitud TXT Relacionada")
    
    def _distribute_vacation_days(self):
        """Distribuye los días de vacaciones entre los períodos disponibles"""
        _logger.info("=== INICIANDO DISTRIBUCIÓN DE DÍAS ===")
        
        for leave in self:
            _logger.info(f"Procesando solicitud ID: {leave.id}, Empleado: {leave.employee_id.name}, Días: {leave.number_of_days}")
            
            if not (leave.holiday_status_id.is_vacation and 
                leave.employee_id and 
                leave.number_of_days > 0):
                _logger.info("No cumple condiciones, saltando")
                continue
                
            # Verificar si el tipo de ausencia está marcado como vacación
            _logger.info(f"Tipo de ausencia: {leave.holiday_status_id.name}, Es vacación: {leave.holiday_status_id.is_vacation}")
            
            # Eliminar asignaciones existentes para esta solicitud
            if leave.allocation_ids:
                _logger.info(f"Eliminando {len(leave.allocation_ids)} asignaciones existentes")
                leave.allocation_ids.unlink()
            
            # Obtener períodos ordenados por antigüedad (más antiguo primero)
            periods = self.env['hr.vacation.period'].search([
                ('employee_id', '=', leave.employee_id.id)
            ], order='year_start asc')
            
            _logger.info(f"Períodos encontrados: {len(periods)}")
            for i, period in enumerate(periods):
                _logger.info(f"Período {i+1}: {period.display_name}")
            
            days_remaining = leave.number_of_days
            allocation_vals = []
            
            for period in periods:
                if days_remaining <= 0:
                    break
                    
                # Calcular días disponibles en este período
                available_days = period.days_remaining
                
                _logger.info(f"Período {period.id}: Días disponibles: {available_days}, Días por asignar: {days_remaining}")
                
                if available_days <= 0:
                    _logger.info(f"Período {period.id} sin días disponibles, saltando")
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
                    _logger.info(f"Asignando {days_to_take} días al período {period.id}")
            
            if days_remaining > 0:
                error_msg = f"No hay suficientes días disponibles. Faltan {days_remaining} días."
                _logger.error(error_msg)
                raise UserError(error_msg)
            
            # Crear las asignaciones
            if allocation_vals:
                _logger.info(f"Creando {len(allocation_vals)} asignaciones")
                try:
                    self.env['hr.vacation.allocation'].create(allocation_vals)
                    _logger.info("Asignaciones creadas exitosamente")
                except Exception as e:
                    _logger.error(f"Error al crear asignaciones: {str(e)}")
                    raise
            else:
                _logger.warning("No se crearon asignaciones")
            
            _logger.info("DISTRIBUCIÓN COMPLETADA")

    def action_approve(self):
        """Sobrescribir la aprobación para distribuir días automáticamente Y manejar TXT"""
        # Primero manejar las solicitudes de Tiempo por Tiempo
        time_off_in_lieu_leaves = self.filtered(
            lambda l: l.holiday_status_id.is_time_off_in_lieu and 
                    l.employee_id and 
                    not l.time_off_in_lieu_id
        )
        
        for leave in time_off_in_lieu_leaves:
            # Crear la solicitud de TXT relacionada
            txt_vals = {
                'name': f"TXT - {leave.employee_id.name} - {leave.request_date_from}",
                'employee_id': leave.employee_id.id,
                'request_date': fields.Date.today(),
                'request_date_from': leave.request_date_from,
                'request_date_to': leave.request_date_to,
                'number_of_days': leave.number_of_days,
                'state': 'approved',
                'notes': f'Creado automáticamente desde ausencia',
                'leave_id': leave.id,
            }
            txt = self.env['hr.time.off.in.lieu'].create(txt_vals)
            leave.time_off_in_lieu_id = txt.id
        
        # Luego distribuir los días de vacaciones (tu lógica existente)
        vacation_leaves = self.filtered(
            lambda l: l.holiday_status_id.is_vacation and 
                    l.employee_id and 
                    l.number_of_days > 0
        )
        
        for leave in vacation_leaves:
            leave._distribute_vacation_days()
        
        # Llamar al método original
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