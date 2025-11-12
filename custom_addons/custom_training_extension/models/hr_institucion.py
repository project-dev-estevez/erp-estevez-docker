from odoo import models, fields

class HrInstitucion(models.Model):
    _name = 'hr.institucion'
    _description = 'Catálogo de Instituciones'
    _rec_name = 'description' 

    code = fields.Char(string="Clave Institución", required=True)
    description = fields.Char(string="Descripción", required=True)
