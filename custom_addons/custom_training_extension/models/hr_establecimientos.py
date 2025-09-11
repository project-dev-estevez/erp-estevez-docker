from odoo import models, fields

class HrState(models.Model):
    _name = 'hr.establecimientos'
    _description = 'Catálogo de Establecimientosss'

    code = fields.Char(string="Clave Establecimiento", required=True)
    name = fields.Char(string="Nombre", required=True)
