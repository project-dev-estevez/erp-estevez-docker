from odoo import models, fields, api, exceptions, _
from odoo.tools import format_datetime
from odoo.tools import safe_eval

class HrAttendanceGeofence(models.Model):
    _name = "hr.attendance.geofence"
    _description = "Attendance Geofence"
    _order = "id desc"

    name = fields.Char('Nombre', required=True)
    description = fields.Char('Descripción')
    company_id = fields.Many2one(
        'res.company', 'Empresa', required=True,
        default=lambda s: s.env.company.id, index=True)
    employee_ids = fields.Many2many('hr.employee', 'employee_geofence_rel', 'geofence_id', 'emp_id', string='Empleados')
    overlay_paths = fields.Text(string='Rutas')