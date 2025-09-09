from odoo import models, fields

class HrOcupaciones(models.Model):
    _name = 'hr.ocupaciones'
    _description = 'Catálogo de Ocupaciones'

    code = fields.Char(string="Clave Ocupación", required=True)
    description = fields.Char(string="Descripción", required=True)
