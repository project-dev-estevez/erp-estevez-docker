from odoo import fields, models

class HrEmployee(models.Model):
    _inherit = "hr.employee"
    
    project_id = fields.Many2one(
        'project.project',
        string='Proyecto',
        help='Proyecto asignado al empleado'
    )
    
    first_name = fields.Char(string="Primer Nombre")
    second_name = fields.Char(string="Segundo Nombre")
    last_name_1 = fields.Char(string="Apellido Paterno")
    last_name_2 = fields.Char(string="Apellido Materno")
    names = fields.Char(string="Nombre Completo")
