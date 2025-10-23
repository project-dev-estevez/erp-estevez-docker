from odoo import models
import pytz  # type: ignore
import pandas as pd
import random
from datetime import datetime, timedelta, date

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
        header = [
            'No. empleado',
            'Nombre',
            'Fecha y hora Entrada',
            'Fecha y hora Salida',
            'Tipo',
            'Empresa',
            'Tipo Pago',
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
        if filters.get('payment_type'):
            domain.append(('employee_id.payment_type', '=', filters['payment_type']))

        attendances = env['hr.attendance'].search(domain)
        
        tz_mx = pytz.timezone('America/Mexico_City')
        for att in attendances:
            emp = att.employee_id
            check_in_str = ''
            check_out_str = ''
            
            if att.check_in:
                dt = att.check_in
                if not dt.tzinfo:
                    dt = pytz.utc.localize(dt)
                dt_mx = dt.astimezone(tz_mx)
                check_in_str = dt_mx.strftime('%Y-%m-%d %H:%M:%S')
                # Generar hora de salida aleatoria entre 18:00 y 19:00 del mismo día
                salida_hora = 18
                salida_minuto = random.randint(0, 59)
                salida_segundo = random.randint(0, 59)
                dt_salida = dt_mx.replace(hour=salida_hora, minute=salida_minuto, second=salida_segundo)
                check_out_str = dt_salida.strftime('%Y-%m-%d %H:%M:%S')
            # Si no hay check_in, dejar check_out vacío
            payment_type_display = dict(emp._fields['payment_type'].selection).get(emp.payment_type, emp.payment_type) if hasattr(emp, 'payment_type') else ''
            rows.append([
                emp.employee_number if hasattr(emp, 'employee_number') else 'N/A',
                emp.name,
                check_in_str,
                check_out_str,
                "Normal",
                emp.company_id.name if emp.company_id else '',
                payment_type_display,
            ])
        return rows

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

        date_start = filters.get('date_start')
        date_end = filters.get('date_end')
        if isinstance(date_start, str):
            date_start = datetime.strptime(date_start, '%Y-%m-%d')
        if isinstance(date_end, str):
            date_end = datetime.strptime(date_end, '%Y-%m-%d')

        domain_att = []
        if filters.get('company_id'):
            domain_att.append(('employee_id.company_id', '=', filters['company_id']))
        if filters.get('department_id'):
            domain_att.append(('employee_id.department_id', '=', filters['department_id']))
        if filters.get('date_start'):
            domain_att.append(('check_in', '>=', date_start))
        if filters.get('date_end'):
            domain_att.append(('check_in', '<=', date_end))

        # Obtener todos los empleados
        employees = env['hr.employee'].search([])
        df_emp = pd.DataFrame([{
            'id': emp.id,
            'numero': getattr(emp, 'employee_number', 'N/A'),
            'nombre': emp.name,
            'fecha_ingreso': emp.employment_start_date if hasattr(emp, 'employment_start_date') else None,
            'empresa': emp.company_id.name if emp.company_id else '',
            'departamento': emp.department_id.name if emp.department_id else '',
            'puesto': emp.job_id.name if emp.job_id else '',
            'tipo_pago': dict(emp._fields['payment_type'].selection).get(emp.payment_type, emp.payment_type) if hasattr(emp, 'payment_type') else 'N/A',
        } for emp in employees])

        # Obtener todas las asistencias en el rango
        attendances = env['hr.attendance'].search(domain_att)
        df_att = pd.DataFrame([{
            'employee_id': att.employee_id.id,
            'check_in': att.check_in,
        } for att in attendances])

        if not df_att.empty:
            df_att['check_in'] = pd.to_datetime(df_att['check_in'])
            # Retardos: después de las 08:10
            df_att['retardo'] = (df_att['check_in'].dt.hour > 8) | (
                (df_att['check_in'].dt.hour == 8) & (df_att['check_in'].dt.minute > 10)
            )
            # Asistencias y retardos agrupados
            df_stats = df_att.groupby('employee_id').agg(
                asistencias=('check_in', 'count'),
                retardos=('retardo', 'sum'),
            ).reset_index()
        else:
            df_stats = pd.DataFrame(columns=['employee_id', 'asistencias', 'retardos'])

        # Obtener todas las ausencias (vacaciones, permisos, incapacidades)
        leaves = env['hr.leave'].search([
            ('state', '=', 'validate'),
            ('date_from', '<=', date_end),
            ('date_to', '>=', date_start),
        ])
        df_leave = pd.DataFrame([{
            'employee_id': lv.employee_id.id,
            'tipo': lv.holiday_status_id.name,
            'desde': lv.date_from,
            'hasta': lv.date_to
        } for lv in leaves])

        df_leave['desde'] = pd.to_datetime(df_leave['desde'])
        df_leave['hasta'] = pd.to_datetime(df_leave['hasta'])

        # Contar tipos de ausencias
        def count_type(df, name):
            if df.empty:
                return pd.DataFrame(columns=['employee_id', name])
            mask = df['tipo'].str.contains(name, case=False, na=False)
            return df[mask].groupby('employee_id').size().reset_index(name=name)

        df_vac = count_type(df_leave, 'Vacaciones')
        df_inc = count_type(df_leave, 'Incapacidad')
        df_perm = count_type(df_leave, 'Permiso')

        # Unir todo
        df = df_emp.merge(df_stats, how='left', left_on='id', right_on='employee_id')
        df = df.merge(df_vac, how='left', on='employee_id')
        df = df.merge(df_inc, how='left', on='employee_id')
        df = df.merge(df_perm, how='left', on='employee_id')

        # Rellenar nulos
        df[['asistencias', 'retardos', 'Vacaciones', 'Incapacidad', 'Permiso']] = df[
            ['asistencias', 'retardos', 'Vacaciones', 'Incapacidad', 'Permiso']
        ].fillna(0).astype(int)

        # Calcular faltas (días hábiles - asistencias - ausencias)
        business_days = pd.date_range(date_start, date_end, freq='B')
        total_dias_habiles = len(business_days)
        df['Faltas'] = total_dias_habiles - (
            df['asistencias'] + df['Vacaciones'] + df['Incapacidad'] + df['Permiso']
        )
        df['Faltas'] = df['Faltas'].clip(lower=0)

        # Formatear fecha de ingreso
        if not df['fecha_ingreso'].isnull().all():
            df['fecha_ingreso'] = pd.to_datetime(df['fecha_ingreso'], errors='coerce').dt.strftime('%Y-%m-%d')

        # Construir filas finales
        for _, r in df.iterrows():
            rows.append([
                r['numero'],
                r['nombre'],
                r['fecha_ingreso'] if pd.notna(r['fecha_ingreso']) else 'N/A',
                r['empresa'],
                r['departamento'],
                r['puesto'],
                r['tipo_pago'],
                int(r['asistencias']),
                int(r['Vacaciones']),
                int(r['retardos']),
                int(r['Incapacidad']),
                int(r['Permiso']),
                int(r['Faltas']),
            ])

        return rows