from odoo import models, fields, api

class ResUsers(models.Model):
    _inherit = 'res.users'

    employee_project_name = fields.Char(
        string='Proyecto',
        compute='_compute_employee_project_name',
        store=False
    )
    employee_number_display = fields.Char(
        string='N° Empleado',
        compute='_compute_employee_number_display',
        store=False
    )
    area_id = fields.Many2one(
        'hr.area',
        string='Área',
        compute='_compute_employee_area',
        store=False
    )
    direction_id = fields.Many2one(
        'hr.direction',
        string='Dirección',
        compute='_compute_employee_direction',
        store=False
    )

    @api.depends('employee_id')
    def _compute_employee_project_name(self):
        for user in self:
            project_name = ''
            if user.employee_id and hasattr(user.employee_id, 'project_id') and user.employee_id.project_id:
                project_name = user.employee_id.project_id.display_name
            user.employee_project_name = project_name

    @api.depends('employee_id')
    def _compute_employee_number_display(self):
        for user in self:
            number = ''
            if user.employee_id and hasattr(user.employee_id, 'employee_number'):
                number = user.employee_id.employee_number or ''
            user.employee_number_display = number

    @api.depends('employee_id')
    def _compute_employee_area(self):
        for user in self:
            area = False
            if user.employee_id and hasattr(user.employee_id, 'area_id'):
                area = user.employee_id.area_id
            user.area_id = area

    @api.depends('employee_id')
    def _compute_employee_direction(self):
        for user in self:
            direction = False
            if user.employee_id and hasattr(user.employee_id, 'direction_id'):
                direction = user.employee_id.direction_id
            user.direction_id = direction