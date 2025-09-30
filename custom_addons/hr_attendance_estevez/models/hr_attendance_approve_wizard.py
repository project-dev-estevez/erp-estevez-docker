from odoo import models, fields, api

class HrAttendanceApproveWizard(models.TransientModel):
    _name = 'hr.attendance.approve.wizard'
    _description = 'Wizard para aprobar asistencia'

    attendance_id = fields.Many2one('hr.attendance', string='Asistencia', required=True)
    observation = fields.Text(string='Observación', required=False)

    def action_confirm_approve(self):
        self.ensure_one()
        attendance = self.attendance_id
        attendance.status = 'approved'
        if self.observation:
            attendance.message_post(body=f"Asistencia aprobada. Observación: {self.observation}")
        else:
            attendance.message_post(body="Asistencia aprobada.")
        return [
            {'type': 'ir.actions.act_window_close'},
            {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'type': 'success',
                    'title': 'Aprobación registrada',
                    'message': 'La asistencia fue aprobada correctamente.',
                    'sticky': False,
                }
            }
        ]
