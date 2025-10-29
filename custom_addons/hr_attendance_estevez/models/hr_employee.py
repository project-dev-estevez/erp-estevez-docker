
import re
from datetime import date, timedelta
import pandas as pd # type: ignore
from odoo import api, fields, models
from odoo.http import request
from odoo.tools import date_utils
import logging
_logger = logging.getLogger(__name__)

class HrEmployee(models.Model):
    """Extiende el modelo hr.employee para incluir métodos
    relacionados con los datos de ausencias para el dashboard."""
    _inherit = 'hr.employee'
    _check_company_auto = True

    # ==========================
    # Métodos públicos
    # ==========================

    @api.model
    def get_employee_leave_data(self):
        """Obtiene datos de ausencias y asistencias para el dashboard."""
        dates = self._get_filtered_dates()
        allowed_company_ids = self._get_allowed_company_ids()
        employees = self.search([('company_id', 'in', allowed_company_ids)])
        employee_data = [
            self._get_single_employee_leave_info(emp, dates)
            for emp in employees
        ]

        return {
            'employee_data': employee_data,
            'filtered_duration_dates': dates[::-1],
        }

    # ==========================
    # Métodos privados auxiliares
    # ==========================

    def _get_filtered_dates(self):
        """Retorna la lista de fechas desde el primer día del mes hasta hoy."""
        today = fields.Date.today()
        start = date_utils.start_of(today, 'month')
        end = today
        return pd.date_range(start, end, freq='d').strftime("%Y-%m-%d").tolist()

    def _get_allowed_company_ids(self):
        """Obtiene los IDs de compañías permitidas a partir de las cookies."""
        cids = request.httprequest.cookies.get('cids', '')
        return [int(cid) for cid in re.split(r'[,-]', cids) if cid.isdigit()]

    def _get_single_employee_leave_info(self, employee, dates):
        """Obtiene la información de ausencias y asistencias para un empleado."""
        leave_records = self._get_validated_leaves(employee.id, dates[0], dates[-1]) if dates else []
        leave_map = self._build_leave_map(leave_records, dates)

        present_dates = {str(att.check_in.date()) for att in employee.attendance_ids}
        leave_data, total_absent_count = self._generate_leave_data(dates, present_dates, leave_map)

        return {
            'id': employee.id,
            'name': employee.name,
            'leave_data': leave_data[::-1],
            'total_absent_count': total_absent_count,
        }

    def _get_validated_leaves(self, employee_id, date_start, date_end):
        """Obtiene los permisos validados del empleado en el rango de fechas."""
        return self.env['hr.leave'].search_read(
            [
                ('state', '=', 'validate'),
                ('employee_id', '=', employee_id),
                ('request_date_to', '>=', date_start),
                ('request_date_from', '<=', date_end),
            ],
            ['request_date_from', 'request_date_to', 'holiday_status_id']
        )

    def _build_leave_map(self, leave_records, dates):
        """Construye un mapa con las fechas de permisos y sus códigos/colores."""
        leave_map = {}
        for leave in leave_records:
            leave_type = self.env['hr.leave.type'].browse(leave['holiday_status_id'][0])
            leave_dates = pd.date_range(
                leave['request_date_from'], leave['request_date_to'], freq='d'
            ).strftime("%Y-%m-%d").tolist()

            for leave_date in leave_dates:
                if leave_date in dates:
                    leave_map[leave_date] = {
                        'code': leave_type.code_id,
                        'color': self._resolve_leave_color(leave_type.color),
                    }
        return leave_map

    def _resolve_leave_color(self, color_code):
        """Devuelve el color hexadecimal correspondiente al código de color."""
        color_map = {
            1: "#F06050", 2: "#F4A460", 3: "#F7CD1F", 4: "#6CC1ED", 5: "#814968",
            6: "#EB7E7F", 7: "#2C8397", 8: "#475577", 9: "#D6145F", 10: "#30C381",
            11: "#9365B8"
        }
        return color_map.get(color_code, "#ffffff")

    def _generate_leave_data(self, dates, present_dates, leave_map):
        """Genera los datos diarios de asistencia/ausencia."""
        leave_data = []
        total_absent_count = 0

        for leave_date in dates:
            if leave_date in leave_map:
                leave_info = leave_map[leave_date]
                state = leave_info['code']
                color = leave_info['color'] 
                total_absent_count += 1
            else:
                state = '✅' if leave_date in present_dates else '❌'
                color = "#ffffff"

            leave_data.append({
                'leave_date': leave_date,
                'state': state,
                'color': color,
            })

        return leave_data, total_absent_count