from odoo import models, fields, api
from datetime import datetime
import logging
import traceback

_logger = logging.getLogger(__name__)

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
    
    # Estados simplificados
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('confirm', 'Por Aprobar'),
        ('validate', 'Aprobado'),
        ('refuse', 'Rechazado')
    ], string='Estado', default='validate', tracking=True)
    
    leave_id = fields.Many2one('hr.leave', string='Ausencia Relacionada', readonly=True)

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
        
        # Forzar estado a "Aprobado" si no se especifica otro
        if 'state' not in vals:
            vals['state'] = 'validate'
        
        # Crear primero la incapacidad
        incapacity = super(HrIncapacity, self).create(vals)
        
        # Luego crear la ausencia relacionada
        incapacity._create_related_leave()
        
        return incapacity

    def write(self, vals):
        result = super(HrIncapacity, self).write(vals)
        
        # Si se modifican fechas o empleado, actualizar la ausencia relacionada
        if any(field in vals for field in ['start_date', 'end_date', 'employee_id', 'state']):
            for record in self:
                if record.leave_id:
                    record._update_related_leave()
        
        return result

    def unlink(self):
        # Eliminar las ausencias relacionadas primero
        for record in self:
            if record.leave_id:
                record.leave_id.unlink()
        return super(HrIncapacity, self).unlink()

    def _create_related_leave(self):
        """Crear una ausencia relacionada en hr.leave"""
        try:
            _logger.info("Creando ausencia relacionada para incapacidad: %s", self.name)
            
            leave_type = self._get_default_holiday_status()
            if not leave_type:
                _logger.error("No se pudo encontrar o crear el tipo de ausencia para incapacidades")
                return
                
            _logger.info("Tipo de ausencia: %s", leave_type.name)
            
            # Convertir fechas a datetime para hr.leave
            date_from = fields.Datetime.to_datetime(self.start_date) if self.start_date else False
            date_to = fields.Datetime.to_datetime(self.end_date) if self.end_date else False
            
            _logger.info("Fecha inicio: %s, Fecha fin: %s", date_from, date_to)
            
            if date_from and date_to:
                # Añadir horas por defecto
                date_from = date_from.replace(hour=8, minute=0, second=0)
                date_to = date_to.replace(hour=17, minute=0, second=0)
                
                leave_vals = {
                    'name': f'Incapacidad: {self.name}',
                    'employee_id': self.employee_id.id,
                    'holiday_status_id': leave_type.id,
                    'date_from': date_from,
                    'date_to': date_to,
                    'request_unit_hours': False,
                    'state': 'confirm',  # Crear en estado "Por Aprobar" primero
                }
                
                _logger.info("Valores para la ausencia: %s", leave_vals)
                
                # Crear la ausencia
                leave = self.env['hr.leave'].create(leave_vals)
                
                # Si la incapacidad está aprobada, aprobar la ausencia también
                if self.state == 'validate':
                    # Usar sudo() para evitar problemas de permisos
                    leave.sudo().action_approve()
                    # Si requiere segunda aprobación
                    if leave.state == 'validate1':
                        leave.sudo().action_validate()
                
                self.leave_id = leave.id
                _logger.info("Ausencia creada exitosamente: %s con estado: %s", leave.id, leave.state)
                
        except Exception as e:
            _logger.error("Error al crear ausencia relacionada: %s", str(e))
            _logger.error("Traceback: %s", traceback.format_exc())

    def _update_related_leave(self):
        """Actualizar la ausencia relacionada en hr.leave"""
        if self.leave_id:
            try:
                # Convertir fechas a datetime para hr.leave
                date_from = fields.Datetime.to_datetime(self.start_date) if self.start_date else False
                date_to = fields.Datetime.to_datetime(self.end_date) if self.end_date else False
                
                if date_from and date_to:
                    date_from = date_from.replace(hour=8, minute=0, second=0)
                    date_to = date_to.replace(hour=17, minute=0, second=0)
                    
                    # Actualizar los campos básicos
                    self.leave_id.write({
                        'employee_id': self.employee_id.id,
                        'date_from': date_from,
                        'date_to': date_to,
                    })
                    
                    # Sincronizar estados usando sudo() para evitar problemas de permisos
                    if self.state == 'validate' and self.leave_id.state != 'validate':
                        self.leave_id.sudo().action_approve()
                        if self.leave_id.state == 'validate1':
                            self.leave_id.sudo().action_validate()
                    elif self.state == 'refuse' and self.leave_id.state != 'refuse':
                        self.leave_id.sudo().action_refuse(f'Rechazado desde incapacidad {self.name}')
                    elif self.state == 'confirm' and self.leave_id.state not in ['confirm', 'validate1']:
                        # Para volver a "Por Aprobar" necesitamos resetear
                        if self.leave_id.state in ['validate', 'refuse']:
                            self.leave_id.sudo().action_draft()
                        self.leave_id.sudo().action_confirm()
                    elif self.state == 'draft' and self.leave_id.state != 'draft':
                        self.leave_id.sudo().action_draft()
                        
            except Exception as e:
                _logger.error("Error al actualizar ausencia relacionada: %s", str(e))
                _logger.error("Traceback: %s", traceback.format_exc())

    def _get_default_holiday_status(self):
        """Obtener o crear el tipo de ausencia para incapacidades"""
        # Buscar el tipo de ausencia para incapacidades
        leave_type = self.env.ref('hr_incapacity.hr_leave_type_incapacity', False)
        if not leave_type:
            # Si no existe, buscar por nombre
            leave_type = self.env['hr.leave.type'].search([('name', 'ilike', 'incapacidad')], limit=1)
            if not leave_type:
                # Crear uno nuevo si no existe
                leave_type = self.env['hr.leave.type'].sudo().create({
                    'name': 'Incapacidad',
                    'requires_allocation': 'no',
                    'color_name': 'red',
                })
        return leave_type

    def action_confirm(self):
        """Mover a estado Por Aprobar"""
        self.write({'state': 'confirm'})
        if self.leave_id:
            self.leave_id.sudo().action_confirm()

    def action_validate(self):
        """Aprobar la incapacidad"""
        self.write({'state': 'validate'})
        if self.leave_id:
            self.leave_id.sudo().action_approve()
            if self.leave_id.state == 'validate1':
                self.leave_id.sudo().action_validate()

    def action_refuse(self):
        """Rechazar la incapacidad"""
        self.write({'state': 'refuse'})
        if self.leave_id:
            self.leave_id.sudo().action_refuse(f'Rechazado desde incapacidad {self.name}')

    def action_draft(self):
        """Volver a borrador"""
        self.write({'state': 'draft'})
        if self.leave_id:
            self.leave_id.sudo().action_draft()