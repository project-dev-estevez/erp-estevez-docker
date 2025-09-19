import logging
from odoo import models, fields

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    incapacity_ids = fields.One2many('hr.incapacity', 'employee_id', string='Incapacidades')
    incapacity_count = fields.Integer(string='Conteo de Incapacidades', compute='_compute_incapacity_count')

    def _compute_incapacity_count(self):
        for employee in self:
            employee.incapacity_count = len(employee.incapacity_ids)

    def action_view_incapacity(self):
        self.ensure_one()
        return {
            'name': 'Incapacidades',
            'type': 'ir.actions.act_window',
            'res_model': 'hr.incapacity',
            'view_mode': 'form',
            'domain': [('employee_id', '=', self.id)],
            'context': {
                'default_employee_id': self.id,
            },
            'target': 'new',
        }