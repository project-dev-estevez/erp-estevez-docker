from odoo import models, fields

class HrOccupation(models.Model):
    _name = 'hr.occupation'
    _description = 'Catálogo de Ocupaciones'

    code = fields.Char(string="Clave Ocupación", required=True)
    description = fields.Char(string="Descripción", required=True)
