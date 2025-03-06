# models/hr_employee.py
from odoo import models, fields

class HrEmployee(models.Model):
    _inherit = "hr.employee"
    
    display_name = fields.Char(compute="_compute_display_name", store=True)
    
    def _compute_display_name(self):
        for employee in self:
            employee.display_name = f"{employee.name} ({employee.job_id.name})" if employee.job_id else employee.name