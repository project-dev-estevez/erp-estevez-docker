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

    def _attendance_action_change(self, geo_information=None):
        """Check In/Check Out action mejorado para evitar cerrar check-ins de días anteriores y marcar cierre automático si corresponde."""
        self.ensure_one()
        action_date = fields.Datetime.now()

        attendance = self.env['hr.attendance'].search([
            ('employee_id', '=', self.id),
            ('check_out', '=', False)
        ], order='check_in desc', limit=1)

        if attendance:
            last_check_in_date = fields.Datetime.context_timestamp(self, attendance.check_in).date()
            today = fields.Datetime.context_timestamp(self, action_date).date()
            if last_check_in_date < today:
                # Cerrar el check-in anterior como automático (check_out = check_in)
                self.env['hr.attendance'].close_attendance_as_auto(attendance)
                # Crear nuevo registro (check-in)
                vals = {
                    'employee_id': self.id,
                    'check_in': action_date,
                }
                if geo_information:
                    vals.update({'in_%s' % key: geo_information[key] for key in geo_information})
                return self.env['hr.attendance'].create(vals)
            else:
                # Si es de hoy, hacer check-out
                if geo_information:
                    attendance.write({
                        'check_out': action_date,
                        **{'out_%s' % key: geo_information[key] for key in geo_information}
                    })
                else:
                    attendance.write({'check_out': action_date})
                return attendance
        else:
            # No hay registro abierto, crear uno nuevo (check-in)
            vals = {
                'employee_id': self.id,
                'check_in': action_date,
            }
            if geo_information:
                vals.update({'in_%s' % key: geo_information[key] for key in geo_information})
            return self.env['hr.attendance'].create(vals)

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