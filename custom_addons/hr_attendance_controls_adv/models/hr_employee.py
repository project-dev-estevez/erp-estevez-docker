from odoo import fields, models, api, _

class HrEmployee(models.Model):
    _inherit = "hr.employee"
    
    user_faces = fields.One2many("hr.employee.faces", "employee_id", "Faces")

class HrEmployeeFaces(models.Model):
    _name = "hr.employee.faces"
    _description = "Face Recognition Images"
    _inherit = ['image.mixin']
    _order = 'id'

    name = fields.Char("Name", related='employee_id.name')
    image = fields.Binary("Images")
    descriptor = fields.Text(string='Face Descriptor')
    has_descriptor = fields.Boolean(string="Has Face Descriptor",default=False, compute='_compute_has_descriptor', readonly=True, store=True)
    employee_id = fields.Many2one("hr.employee", "User", index=True, ondelete='cascade')

    @api.depends('descriptor')
    def _compute_has_descriptor(self):
        for rec in self:
            rec.has_descriptor = True if rec.descriptor else False