from odoo import fields, models, api, _

class HrEmployee(models.Model):
    _inherit = "hr.employee"
    
    user_faces = fields.One2many("hr.employee.faces", "employee_id", "Caras")

    attendance_status = fields.Selection([
        ('pre_work', 'Pre-work'),
        ('in_work', 'In work'),
        ('post_work', 'Post-work'),
    ], string="Estado de asistencia", compute='_compute_attendance_status', store=False)

    @api.depends('attendance_ids.check_in', 'attendance_ids.check_out')
    def _compute_attendance_status(self):
        for employee in self:
            today = fields.Date.context_today(employee)
            attendances_today = employee.attendance_ids.filtered(
                lambda a: a.check_in and
                fields.Datetime.context_timestamp(employee, a.check_in).date() == today
            )
            if not attendances_today:
                employee.attendance_status = 'pre_work'
            else:
                attendance = attendances_today.sorted('check_in', reverse=True)[0]
                if attendance.check_out:
                    employee.attendance_status = 'post_work'
                else:
                    employee.attendance_status = 'in_work'

class HrEmployeeFaces(models.Model):
    _name = "hr.employee.faces"
    _description = "Face Recognition Images"
    _inherit = ['image.mixin']
    _order = 'id'

    name = fields.Char("Nombre", related='employee_id.name')
    image = fields.Binary("Imagenes")
    descriptor = fields.Text(string='Face Descriptor')
    has_descriptor = fields.Boolean(string="Has Face Descriptor",default=False, compute='_compute_has_descriptor', readonly=True, store=True)
    employee_id = fields.Many2one("hr.employee", "User", index=True, ondelete='cascade')

    @api.depends('descriptor')
    def _compute_has_descriptor(self):
        for rec in self:
            rec.has_descriptor = True if rec.descriptor else False