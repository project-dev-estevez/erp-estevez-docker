from odoo import models, fields

class HrState(models.Model):
    _name = 'hr.agente'
    _description = 'Catálogo de Agentes'

    code = fields.Char(string="Clave Agente", required=True)
    description = fields.Char(string="Descripción", required=True)
