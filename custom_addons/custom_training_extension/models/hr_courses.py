from odoo import models, fields

class HrCourses(models.Model):
    _name = 'hr.courses'
    _description = 'Catálogo de Cursos'

    code = fields.Char(string="Clave Curso", required=True)
    description = fields.Char(string="Descripción", required=True)    
