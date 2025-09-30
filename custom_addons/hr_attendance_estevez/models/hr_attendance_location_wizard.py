from odoo import models, fields, api

class HrAttendanceLocationWizard(models.TransientModel):
    _name = 'hr.attendance.location.wizard'
    _description = 'Wizard para mostrar ubicación de check-in'

    check_in_latitude = fields.Float(string='Latitud')
    check_in_longitude = fields.Float(string='Longitud')
    map_iframe = fields.Html(string="Mapa", compute="_compute_map_iframe", sanitize=False)

    @api.depends('check_in_latitude', 'check_in_longitude')
    def _compute_map_iframe(self):
        for wizard in self:
            if wizard.check_in_latitude and wizard.check_in_longitude:
                lat, lng = wizard.check_in_latitude, wizard.check_in_longitude
                url = (
                    f"https://www.openstreetmap.org/export/embed.html?"
                    f"bbox={lng-0.001},{lat-0.001},{lng+0.001},{lat+0.001}"
                    f"&layer=mapnik&marker={lat},{lng}"
                )
                wizard.map_iframe = f"""
                    <iframe width="100%" height="400" frameborder="0" 
                            scrolling="no" marginheight="0" marginwidth="0"
                            src="{url}"></iframe>
                """
            else:
                wizard.map_iframe = "<p>No hay coordenadas disponibles.</p>"

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        attendance = self.env['hr.attendance'].browse(self.env.context.get('attendance_id'))
        if self.env.context.get('is_checkout'):
            res['check_in_latitude'] = attendance.check_out_latitude
            res['check_in_longitude'] = attendance.check_out_longitude
        else:
            res['check_in_latitude'] = attendance.check_in_latitude
            res['check_in_longitude'] = attendance.check_in_longitude
        return res
