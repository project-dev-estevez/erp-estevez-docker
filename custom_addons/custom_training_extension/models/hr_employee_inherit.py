from odoo import models, fields

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    state_id = fields.Many2one('hr.state', string="Estado")
    municipality_id = fields.Many2one('hr.municipality', string="Municipio")
    occupation_id = fields.Many2one('hr.occupation', string="Ocupación")
