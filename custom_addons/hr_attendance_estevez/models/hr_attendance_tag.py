from odoo import models, fields

class HrAttendanceTag(models.Model):
    _name = 'hr.attendance.tag'
    _description = 'Etiqueta de Asistencia'

    name = fields.Char('Nombre', required=True, unique=True)
    color = fields.Integer('Color')  # Opcional, para visualización
