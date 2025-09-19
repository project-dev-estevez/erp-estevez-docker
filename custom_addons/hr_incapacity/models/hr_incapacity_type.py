import logging
from odoo import models, fields

class HrIncapacityType(models.Model):
    _name = 'hr.incapacity.type'
    _description = 'Tipos de Incapacidad'

    name = fields.Char(string='Tipo de Incapacidad', required=True)
    code = fields.Char(string='Código', required=True)
    description = fields.Text(string='Descripción')