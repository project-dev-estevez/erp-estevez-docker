from odoo import models, fields

class HrJob(models.Model):
    _inherit = 'hr.job'

    area_id = fields.Many2one('hr.area', string='Área')
    department_ids = fields.One2many('hr.department', 'direction_id', string='Departamentos')
    job_id = fields.Many2one('hr.job', string='Puesto')
    director_id = fields.Many2one('hr.employee', string='Director')
    direction_id = fields.Many2one('hr.direction', string='Dirección')
    company_id = fields.Many2one('res.company', string='Empresa')