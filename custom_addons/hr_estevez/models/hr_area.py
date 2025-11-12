from odoo import api, models, fields

class HrArea(models.Model):
    _name = 'hr.area'
    _description = 'Area'

    name = fields.Char('Nombre', required=True)
    company_id = fields.Many2one('res.company', string='Empresa', ondelete='set null', readonly=True)
    department_id = fields.Many2one('hr.department', string='Departamento')
    employee_ids = fields.One2many('hr.employee', 'area_id', string='Empleados')
    coordinator_id = fields.Many2one('hr.employee', string='Coordinador')
    direction_id = fields.Many2one('hr.direction', string='Dirección')
    job_id = fields.Many2one('hr.job', string='Puesto')
    area_ids = fields.One2many('hr.area', 'department_id', string='Áreas')
    total_employees = fields.Integer(string='Total Empleados', compute='_compute_total_employees')

    @api.onchange('department_id')
    def _onchange_department_id(self):
        if self.department_id:
            self.company_id = self.department_id.company_id

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'department_id' in vals:
             department = self.env['hr.department'].browse(vals['department_id'])
             vals['company_id'] = department.company_id.id
        return super(HrArea, self).create(vals_list)

    def write(self, vals):
        if 'department_id' in vals:
            department = self.env['hr.department'].browse(vals['department_id'])
            vals['company_id'] = department.company_id.id
        return super(HrArea, self).write(vals)

    
    @api.depends('employee_ids')
    def _compute_total_employees(self):
        for area in self:
            area.total_employees = len(area.employee_ids)
            
            
            
