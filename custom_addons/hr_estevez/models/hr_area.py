from odoo import api, models, fields

class HrArea(models.Model):
    _name = 'hr.area'
    _description = 'Area'

    name = fields.Char('Nombre', required=True)
    company_id = fields.Many2one('res.company', string='Empresa', ondelete='set null', readonly=True)
    department_id = fields.Many2one('hr.department', string='Departamento')
    employee_ids = fields.One2many('hr.employee', 'area_id', string='Empleados')

    @api.onchange('department_id')
    def _onchange_department_id(self):
        if self.department_id:
            self.company_id = self.department_id.company_id

    @api.model
    def create(self, vals):
        if 'department_id' in vals:
            department = self.env['hr.department'].browse(vals['department_id'])
            vals['company_id'] = department.company_id.id
        return super(HrArea, self).create(vals)

    def write(self, vals):
        if 'department_id' in vals:
            department = self.env['hr.department'].browse(vals['department_id'])
            vals['company_id'] = department.company_id.id
        return super(HrArea, self).write(vals)