# -*- coding: utf-8 -*-

from odoo import models, fields

class HrDirection(models.Model):
    _name = 'hr.direction'
    _description = 'Direction'

    name = fields.Char('Nombre', required=True)
    director_id = fields.Many2one('hr.employee', string='Director')
    parent_id = fields.Many2one('hr.direction', string='Dirección Padre')
    child_ids = fields.One2many('hr.direction', 'parent_id', string='Direcciones Hijas')
    company_id = fields.Many2one('res.company', string='Empresa', ondelete='set null')
    department_ids = fields.One2many('hr.department', 'direction_id', string='Departamentos')