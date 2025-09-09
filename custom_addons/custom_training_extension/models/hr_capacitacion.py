from odoo import models, fields

class HrCapacitacion(models.Model):
    _name = 'hr.capacitacion'
    _description = 'Catálogo de Capacitaciones'

    code = fields.Char(string="Clave Capacitación", required=True)
    description = fields.Char(string="Nombre", required=True)
