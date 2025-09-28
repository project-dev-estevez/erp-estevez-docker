from odoo import models, fields, api

class HrAttendancePhotoWizard(models.TransientModel):
    _name = 'hr.attendance.photo.wizard'
    _description = 'Wizard para mostrar foto de check-in'

    check_in_photo = fields.Binary(string='Foto de Check-in')

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        attendance = self.env['hr.attendance'].browse(self.env.context.get('attendance_id'))
        res['check_in_photo'] = attendance.check_in_photo
        return res
