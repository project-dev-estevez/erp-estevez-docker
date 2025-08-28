from odoo import api, fields, models

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    
    hr_attendance_geolocation = fields.Boolean(related="company_id.hr_attendance_geolocation", string="Geolocation", readonly=False)
    hr_attendance_geofence = fields.Boolean(related="company_id.hr_attendance_geofence", string="Geofence", readonly=False)
    hr_attendance_face_recognition = fields.Boolean(related="company_id.hr_attendance_face_recognition", string="Face Recognition", readonly=False)
    hr_attendance_photo = fields.Boolean(related="company_id.hr_attendance_photo", string="Photo", readonly=False)
    hr_attendance_ip = fields.Boolean(related="company_id.hr_attendance_ip", string="IP Address", readonly=False)
    hr_attendance_reason = fields.Boolean(related="company_id.hr_attendance_reason", string="Reason", readonly=False)
    
    hr_attendance_geolocation_k = fields.Boolean(related="company_id.hr_attendance_geolocation_k", string="Geolocation", readonly=False)
    hr_attendance_geofence_k = fields.Boolean(related="company_id.hr_attendance_geofence_k", string="Geofence", readonly=False)
    hr_attendance_face_recognition_k = fields.Boolean(related="company_id.hr_attendance_face_recognition_k", string="Face Recognition", readonly=False)
    hr_attendance_ip_k = fields.Boolean(related="company_id.hr_attendance_ip_k", string="IP Address", readonly=False)


    @api.onchange('hr_attendance_face_recognition')
    def _onchange_face_recognition(self):
        if self.hr_attendance_face_recognition:
            self.hr_attendance_photo = False
    
    @api.onchange('hr_attendance_photo')
    def _onchange_photo(self):
        if self.hr_attendance_photo:
            self.hr_attendance_face_recognition = False
    