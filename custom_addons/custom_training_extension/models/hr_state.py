from odoo import models, fields

class HrState(models.Model):
    _name = 'hr.state'
    _description = 'Catálogo de Estados'

    code = fields.Char(string="Clave Estado", required=True)
    name = fields.Char(string="Nombre Estado", required=True)
