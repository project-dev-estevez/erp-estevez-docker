from odoo import models, fields

class HrProbatorio(models.Model):
    _name = 'hr.probatorio'
    _description = 'Catálogo de Documentos Probatorios'

    code = fields.Char(string="Clave Doc Probatorio", required=True)
    description = fields.Char(string="Descripción", required=True)
