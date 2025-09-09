from odoo import models, fields

class HrModalidad(models.Model):
    _name = 'hr.modalidad'
    _description = 'Catálogo de Modalidades'

    code = fields.Char(string="Clave Modalidad", required=True)
    description = fields.Char(string="Descripción", required=True)
