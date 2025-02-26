from odoo import api, models, fields

class HrDepartment(models.Model):
    _inherit = 'hr.department'

    area_ids = fields.One2many('hr.area', 'department_id', string='Áreas')
    direction_id = fields.Many2one('hr.direction', string='Dirección')

    parent_id = fields.Many2one('hr.department', string='Parent Department', index=True, check_company=True, store=False)
    child_ids = fields.One2many('hr.department', 'parent_id', string='Child Departments', store=False)

    @api.model
    def create(self, vals):
        department = super(HrDepartment, self).create(vals)
        if vals.get('manager_id'):
            manager = self.env['hr.employee'].browse(vals['manager_id'])
            manager.write({'department_id': department.id})
        return department

    def write(self, vals):
        res = super(HrDepartment, self).write(vals)
        if 'manager_id' in vals:
            for department in self:
                manager = self.env['hr.employee'].browse(vals['manager_id'])
                manager.write({'department_id': department.id})
        return res