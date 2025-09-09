from odoo import models, fields

class HrMunicipality(models.Model):
    _name = 'hr.municipality'
    _description = 'Catálogo de Municipios'

    code = fields.Char(string="Clave Municipio", required=True)
    name = fields.Char(string="Nombre Municipio", required=True)
    estado_id = fields.Many2one(
        comodel_name='custom_training_extension.estado',
        string='Estado',        
        ondelete='restrict'
    )
