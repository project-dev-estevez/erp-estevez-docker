from odoo import models, fields

class HrJob(models.Model):
    _inherit = 'hr.job'

    area_id = fields.Many2one('hr.area', string='Area')