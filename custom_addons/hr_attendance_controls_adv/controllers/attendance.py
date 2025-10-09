from odoo import http, _
from odoo.http import request
import datetime
from odoo.addons.hr_attendance.controllers.main import HrAttendance as HrAttendance

class HrAttendance(HrAttendance):

    @staticmethod
    def _get_employee_info_response(employee):
        rslt = super(HrAttendance, HrAttendance)._get_employee_info_response(employee)
        rslt['attendance']['id'] = employee.last_attendance_id.id or False
        return rslt
    
    @staticmethod
    def _get_user_attendance_data(employee):
        response = super(HrAttendance, HrAttendance)._get_user_attendance_data(employee)
        
        if employee:
            response['attendance_status'] = employee.attendance_status
        
        return response
    
    @http.route('/hr_attendance/attendance_user_data', type="json", auth="user", readonly=True)
    def user_attendance_data(self):
        employee = request.env.user.employee_id
        return self._get_user_attendance_data(employee)
    
    @http.route('/hr_attendance/update_checkin_controls', type="json", auth="public")
    def update_checkin_controls(self, token, attendance_id, check_in_latitude, check_in_longitude, check_in_geofence_ids, check_in_photo, check_in_ipaddress):
        company = self._get_company(token)
        attendance = False
        if company:
            attendance = request.env['hr.attendance'].sudo().browse(attendance_id)
            if attendance:
                attendance.sudo().write({
                    'check_in_latitude': check_in_latitude,
                    'check_in_longitude': check_in_longitude,
                    'check_in_geofence_ids': check_in_geofence_ids,
                    'check_in_photo': check_in_photo,
                    'check_in_ipaddress': check_in_ipaddress,
                })
        return attendance
    
    @http.route('/hr_attendance/update_checkout_controls', type="json", auth="public")
    def update_checkout_controls(self, token, attendance_id, check_out_latitude, check_out_longitude, check_out_geofence_ids, check_out_photo, check_out_ipaddress):
        company = self._get_company(token)
        attendance = False
        if company:
            attendance = request.env['hr.attendance'].sudo().browse(attendance_id)
            if attendance:
                attendance.sudo().write({
                    'check_out_latitude': check_out_latitude,
                    'check_out_longitude': check_out_longitude,
                    'check_out_geofence_ids': check_out_geofence_ids,
                    'check_out_photo': check_out_photo,
                    'check_out_ipaddress': check_out_ipaddress,
                })
        return attendance
    
    @http.route('/hr_attendance/attendance_res_config', type="json", auth="public",)
    def attendance_res_config(self, token):
        company = self._get_company(token)
        conf = {}
        if company:
            conf['hr_attendance_geolocation_k'] = company.hr_attendance_geolocation_k
            conf['hr_attendance_geofence_k'] = company.hr_attendance_geofence_k
            conf['hr_attendance_face_recognition_k'] = company.hr_attendance_face_recognition_k
            conf['hr_attendance_ip_k'] = company.hr_attendance_ip_k
        return conf
    
    @http.route('/hr_attendance/get_geofences/', type="json", auth="public")
    def get_geofences(self, employee_id, token):
        if not employee_id:
            return []
        company = self._get_company(token)
        geofences = request.env['hr.attendance.geofence'].sudo().search_read([
            ('company_id', '=', int(company.id)),
            ('employee_ids', 'in',int(employee_id))
            ], ['id', 'name', 'overlay_paths'])
        return geofences
        """
        Verificar si un punto está dentro de un círculo
        Usando fórmula de distancia haversine
        """
        import math
        
        # Radio de la Tierra en metros
        R = 6371000
        
        # Convertir grados a radianes
        lat1 = math.radians(lat)
        lng1 = math.radians(lng)
        lat2 = math.radians(center_lat)
        lng2 = math.radians(center_lng)
        
        # Diferencias
        dlat = lat2 - lat1
        dlng = lng2 - lng1
        
        # Fórmula haversine
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlng/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        distance = R * c
        
        return distance <= radius_meters