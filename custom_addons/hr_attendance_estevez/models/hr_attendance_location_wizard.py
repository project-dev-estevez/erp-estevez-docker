from odoo import models, fields, api

class HrAttendanceLocationWizard(models.TransientModel):
    _name = 'hr.attendance.location.wizard'
    _description = 'Wizard para mostrar ubicación de check-in'

    check_in_latitude = fields.Float(string='Latitud')
    check_in_longitude = fields.Float(string='Longitud')
    geofence_name = fields.Char(string='Geocerca', readonly=True)
    geofence_description = fields.Text(string='Descripción', readonly=True)
    map_iframe = fields.Html(string="Mapa", sanitize=False)

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        attendance_id = self.env.context.get('attendance_id')

        if not attendance_id:
            return res
        
        attendance = self.env['hr.attendance'].browse(attendance_id)
        is_checkout = self.env.context.get('is_checkout')
        
        # Extraer coordenadas y geocerca según el tipo
        lat, lng = self._get_coordinates(attendance, is_checkout)
        geofence_info = self._get_geofence_info(attendance, is_checkout)
        
        # Actualizar resultado
        res.update({
            'check_in_latitude': lat,
            'check_in_longitude': lng,
            'geofence_name': geofence_info['name'],
            'geofence_description': geofence_info['description'],
            'map_iframe': self._generate_map_html(lat, lng)
        })
        
        return res

    def _get_coordinates(self, attendance, is_checkout):
        """Obtiene las coordenadas según el tipo de registro."""
        if is_checkout:
            return attendance.check_out_latitude, attendance.check_out_longitude
        return attendance.check_in_latitude, attendance.check_in_longitude

    def _get_geofence_info(self, attendance, is_checkout):
        """Obtiene información de la geocerca según el tipo de registro."""
        geofence_ids = (attendance.check_out_geofence_ids if is_checkout 
                       else attendance.check_in_geofence_ids)
        
        if not geofence_ids:
            return {
                'name': 'Sin geocerca',
                'description': 'No se registró en una geocerca definida'
            }
        
        geofence = geofence_ids[0]
        return {
            'name': geofence.name,
            'description': geofence.description or 'Sin descripción'
        }

    def _generate_map_html(self, lat, lng):
        """Genera el HTML del mapa de Google Maps."""
        if not (lat and lng):
            return "<p style='text-align:center; color:#666;'>No hay coordenadas disponibles.</p>"
        
        url = f"https://maps.google.com/maps?q={lat},{lng}&hl=es&z=17&output=embed"
        return f"""
            <div style="width: 100%; text-align: center;">
                <iframe width="100%" height="450" frameborder="0" style="border:0"
                        src="{url}"
                        allowfullscreen></iframe>
                <br/>
                <small>
                    <a href="https://www.google.com/maps?q={lat},{lng}" target="_blank" 
                       style="color:#1a73e8; text-decoration:none;">
                        📍 Ver en Google Maps
                    </a>
                </small>
            </div>
        """