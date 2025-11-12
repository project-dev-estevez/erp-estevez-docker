from odoo import models, fields

class HrState(models.Model):
    _name = 'hr.tematicas'
    _description = 'Catálogo de Areas temáticas'
    _rec_name = 'description' 

    code = fields.Char(string="Clave Area Temática", required=True)
    description = fields.Char(string="Descripción", required=True)
