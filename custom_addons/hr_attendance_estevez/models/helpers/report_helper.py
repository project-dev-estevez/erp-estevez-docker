from odoo import models

class ReportHelper(models.AbstractModel):
    _name = 'hr_attendance_estevez.report_helper'
    _description = 'Helpers para reportes de asistencias y nómina'

    def get_report_rows(self, env, report_type='attendance', filters=None):
        """
        Retorna las filas para el tipo de reporte solicitado.
        filters: dict con los filtros del wizard
        """
        filters = filters or {}
        if report_type == 'attendance':
            return self._get_attendance_report_rows(env, filters)
        elif report_type == 'payroll':
            return self._get_payroll_report_rows(env, filters)
        else:
            return []

    def _get_attendance_report_rows(self, env, filters):
        # Aquí puedes usar los filtros si lo necesitas
        return [
            ['Empleado', 'Check-In', 'Check-Out', 'Duración', 'TipoPago'],
            ['Juan Pérez', '2025-10-20 08:00', '2025-10-20 17:00', 9, 'Mensual'],
        ]

    def _get_payroll_report_rows(self, env, filters):
        header = [
            'Numero Empleado',
            'Nombre Completo',
            'Fecha de Ingreso',
            'Empresa',
            'Departamento',
            'Puesto',
            'Tipo Pago',
            'Asistencias',
            'Vacaciones',
            'Retardos',
            'Incapacidades',
            'Permisos',
            'Faltas'
        ]
        rows = [header]

        domain = []
        if filters.get('date_start'):
            domain.append(('check_in', '>=', filters['date_start']))
        if filters.get('date_end'):
            domain.append(('check_in', '<=', filters['date_end']))
        if filters.get('company_id'):
            domain.append(('employee_id.company_id', '=', filters['company_id']))
        if filters.get('department_id'):
            domain.append(('employee_id.department_id', '=', filters['department_id']))

        employees = env['hr.employee'].search([])
        for emp in employees:
            att_domain = domain + [('employee_id', '=', emp.id)]
            attendances = env['hr.attendance'].search(att_domain)
            # Ejemplo de conteos (ajusta según tu lógica real)
            total_asistencias = len(attendances)
            total_vacaciones = env['hr.leave'].search_count([
                ('employee_id', '=', emp.id),
                ('holiday_status_id.name', 'ilike', 'Vacaciones'),
                ('state', '=', 'validate'),
                ('date_from', '>=', filters.get('date_start')),
                ('date_to', '<=', filters.get('date_end')),
            ])
            # Retardos: calcular por check_in > hora estándar (ejemplo: 09:00)
            hora_estandar = filters.get('hora_estandar', '09:00')
            total_retardos = 0
            for att in attendances:
                check_in_dt = att.check_in
                if check_in_dt:
                    # Si check_in es string, conviértelo a datetime
                    if isinstance(check_in_dt, str):
                        from datetime import datetime
                        check_in_dt = datetime.strptime(check_in_dt, '%Y-%m-%d %H:%M:%S')
                    if check_in_dt.strftime('%H:%M') > hora_estandar:
                        total_retardos += 1
            total_incapacidades = env['hr.leave'].search_count([
                ('employee_id', '=', emp.id),
                ('holiday_status_id.name', 'ilike', 'Incapacidad'),
                ('state', '=', 'validate'),
                ('date_from', '>=', filters.get('date_start')),
                ('date_to', '<=', filters.get('date_end')),
            ])
            total_permisos = env['hr.leave'].search_count([
                ('employee_id', '=', emp.id),
                ('holiday_status_id.name', 'ilike', 'Permiso'),
                ('state', '=', 'validate'),
                ('date_from', '>=', filters.get('date_start')),
                ('date_to', '<=', filters.get('date_end')),
            ])
            # Faltas: lógica personalizada, aquí solo ejemplo
            total_faltas = 0

            rows.append([
                emp.employee_number if hasattr(emp, 'employee_number') else '',
                emp.name,
                emp.entry_date if hasattr(emp, 'entry_date') else '',
                emp.company_id.name if emp.company_id else '',
                emp.department_id.name if emp.department_id else '',
                emp.job_id.name if emp.job_id else '',
                emp.contract_id.structure_type_id.name if hasattr(emp, 'contract_id') and emp.contract_id and hasattr(emp.contract_id, 'structure_type_id') and emp.contract_id.structure_type_id else '',
                total_asistencias,
                total_vacaciones,
                total_retardos,
                total_incapacidades,
                total_permisos,
                total_faltas,
            ])

        return rows