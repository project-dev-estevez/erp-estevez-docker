from odoo import http
from odoo.http import request
import base64

class HrAttendanceFaceRecognition(http.Controller):

    @staticmethod
    def _get_kiosk_company(token):
        """Empresa dueña del token de kiosco, o vacío si el token no es válido."""
        if not token:
            return request.env['res.company']
        return request.env['res.company'].sudo().search([('attendance_kiosk_key', '=', token)], limit=1)

    def _get_recognition_employees(self, token):
        """Empleados cuyos rostros puede reconocer quien llama.

        - Kiosco (token): solo empleados de la empresa dueña del token.
        - Usuario autenticado sin token (menú de asistencia): solo su propio empleado
          en la empresa activa, ya que el cliente únicamente acepta esa coincidencia.
        """
        if token:
            company = self._get_kiosk_company(token)
            if not company:
                return request.env['hr.employee']
            return request.env['hr.employee'].sudo().search([('company_id', '=', company.id)])
        user = request.env.user
        if not request.session.uid or user._is_public():
            return request.env['hr.employee']
        return user.employee_ids.filtered(lambda e: e.company_id == request.env.company).sudo()

    @http.route('/hr_attendance_controls_adv/loadLabeledImages/', type='json', auth="public")
    def load_labeled_images(self, token=None):
        descriptions = []
        employees = self._get_recognition_employees(token)
        for employee in employees:
            descriptors = []
            for faces in employee.user_faces:
                if faces.descriptor and faces.descriptor != 'false':
                    descriptors.append(faces.descriptor)
            if descriptors:
                vals = {
                    "label": str(employee.id) +','+ str(employee.name),
                    "descriptors": descriptors,
                }
                descriptions.append(vals)
        return descriptions

    @http.route('/hr_attendance_controls_adv/getName/<int:employee_id>/', type='json', auth="public")
    def get_name(self, employee_id, token=None):
        company = self._get_kiosk_company(token)
        if not employee_id or not company:
            return False
        employee = request.env['hr.employee'].sudo().search([
            ('id', '=', int(employee_id)),
            ('company_id', '=', company.id),
        ], limit=1)
        return employee.name or False
