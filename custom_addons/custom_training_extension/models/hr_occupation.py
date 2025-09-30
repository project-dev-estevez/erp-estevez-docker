from odoo import models, fields

class HrOccupation(models.Model):
    _name = 'hr.occupation'
    _description = 'Catálogo de Ocupaciones'

    code = fields.Char(string="Clave Ocupación", required=True)
    name = fields.Char(string="Descripción", required=True)
    description = fields.Char(string="Descripción")

    employee_ids = fields.One2many(
        comodel_name='hr.employee', 
        inverse_name='occupation_id', 
        string='Empleados'
    )