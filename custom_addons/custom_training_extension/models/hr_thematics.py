from odoo import models, fields

class HrThematics(models.Model):
    _name = 'hr.thematics'
    _description = 'Catálogo de Temáticas'

    code = fields.Char(string="Clave Temática", required=True)
    name = fields.Char(string="Nombre", required=True)
