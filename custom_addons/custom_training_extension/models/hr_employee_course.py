from odoo import models, fields

class HrEmployeeCourse(models.Model):
    _name = 'hr.employee.course'
    _description = 'Relación Empleado - Curso'

    employee_id = fields.Many2one('hr.employee', string="Empleado", required=True)
    course_id = fields.Many2one('slide.channel', string="Curso", required=True)
    date_completed = fields.Date(string="Fecha de finalización")
    score = fields.Float(string="Calificación")
