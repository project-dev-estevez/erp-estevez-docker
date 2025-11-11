from odoo import models, fields

class HrSkillTag(models.Model):
    _name = 'hr.study.tag'
    _description = 'Etiqueta de estatus de estudios'

    name = fields.Char(string='Nombre', required=True)
    color = fields.Integer(string='Color Index')  # para el color en los tags
