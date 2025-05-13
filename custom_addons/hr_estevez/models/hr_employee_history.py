from odoo import models, fields

class HrEmployeeHistory(models.Model):
    _name = 'hr.employee.history'
    _description = 'Historial de Altas y Bajas'

    employee_id = fields.Many2one('hr.employee', string='Empleado', required=True)
    date = fields.Datetime(string='Fecha', required=True)
    status = fields.Selection([
        ('alta', 'Alta'),
        ('baja', 'Baja'),
    ], string='Estado', required=True)
    reason = fields.Text(string='Motivo')
    possible_rehire = fields.Selection([
        ('viable', 'Viable'),
        ('inviable', 'Inviable'),
    ], string='Posible Recontratación')  # Campo opcional para bajas