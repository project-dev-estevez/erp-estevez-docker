from odoo import models, fields, api

class HrAttendanceLogWizard(models.TransientModel):
    _name = 'hr.attendance.log.wizard'
    _description = 'Wizard para ver el log de mensajes de asistencia'

    attendance_id = fields.Many2one('hr.attendance', string='Asistencia', required=True)
    message_ids = fields.One2many('mail.message', compute='_compute_message_ids', string='Mensajes')

    @api.depends('attendance_id')
    def _compute_message_ids(self):
        for wizard in self:
            wizard.message_ids = wizard.attendance_id.message_ids
