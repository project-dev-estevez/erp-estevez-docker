from odoo import models, fields

class HrEstudios(models.Model):
    _name = 'hr.estudios'
    _description = 'Catálogo de Nivel de Estudios'

    code = fields.Char(string="Clave Nivel de Estudios", required=True)
    name = fields.Char(string="Descripción", required=True)
