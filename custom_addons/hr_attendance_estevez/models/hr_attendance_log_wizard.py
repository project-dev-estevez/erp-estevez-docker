from odoo import models, fields, api

class HrAttendanceLogWizard(models.TransientModel):
    _name = 'hr.attendance.log.wizard'
    _description = 'Wizard para ver el log de mensajes de asistencia'

    attendance_id = fields.Many2one('hr.attendance', string='Asistencia', required=True)
    message_ids = fields.One2many('mail.message', compute='_compute_message_ids', string='Mensajes')
    new_message = fields.Text(string='Nuevo Mensaje', help='Escribe un mensaje para agregar al historial')

    @api.depends('attendance_id')
    def _compute_message_ids(self):
        for wizard in self:
            if wizard.attendance_id:
                # Filtrar mensajes que NO tengan body vacío
                messages = wizard.attendance_id.message_ids.filtered(
                    lambda m: m.body and m.body.strip() not in ['', '<p><br></p>', '<p></p>', '<br>', '<br/>']
                )
                wizard.message_ids = messages
            else:
                wizard.message_ids = False
    
    def action_add_message(self):
        """Agregar un nuevo mensaje al registro de asistencia"""
        self.ensure_one()
        if self.new_message and self.new_message.strip():
            # Crear el mensaje en el chatter del registro de asistencia
            self.attendance_id.message_post(
                body=self.new_message,
                message_type='comment',
                subtype_xmlid='mail.mt_note',
            )
            # Limpiar el campo después de agregar
            self.new_message = False
            # Recargar el wizard para mostrar el nuevo mensaje
            return {
                'type': 'ir.actions.act_window',
                'res_model': self._name,
                'res_id': self.id,
                'view_mode': 'form',
                'target': 'new',
                'context': self.env.context,
            }
