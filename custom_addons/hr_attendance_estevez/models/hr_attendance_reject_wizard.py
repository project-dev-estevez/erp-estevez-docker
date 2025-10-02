from odoo import models, fields, api

class HrAttendanceRejectWizard(models.TransientModel):
    _name = 'hr.attendance.reject.wizard'
    _description = 'Wizard para rechazar asistencia'

    attendance_id = fields.Many2one('hr.attendance', string='Asistencia', required=True)
    observation = fields.Text(string='Observación', required=True)

    def action_confirm_reject(self):
        self.ensure_one()
        attendance = self.attendance_id
        attendance.status = 'rejected'
        attendance.message_post(body=f"Asistencia rechazada: {self.observation}")
        return {'type': 'ir.actions.act_window_close'}
