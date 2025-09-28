from odoo import models, fields, api

class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

    checkin_photo = fields.Binary(string='Foto de Check-in')

    def action_show_checkin_photo(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Foto de Ingreso',
            'res_model': 'hr.attendance.photo.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'attendance_id': self.id},
        }

    def action_show_checkin_location(self):
        # Aquí deberías retornar una acción que muestre el mapa con la ubicación
        # Puedes personalizar esto con un wizard o una vista personalizada
        return {
            'type': 'ir.actions.act_window',
            'name': 'Ubicación de Check-in',
            'res_model': 'hr.attendance',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
        }

    def action_accept_checkin(self):
        # Lógica para aceptar el check-in
        self.write({'state': 'accepted'})
        return True

    def action_reject_checkin(self):
        # Lógica para rechazar el check-in y abrir wizard de observación
        return {
            'type': 'ir.actions.act_window',
            'name': 'Rechazar Asistencia',
            'res_model': 'hr.attendance.reject.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_attendance_id': self.id},
        }