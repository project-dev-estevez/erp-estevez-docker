from odoo import models
import pytz  # type: ignore
import pandas as pd # type: ignore
import random
from datetime import datetime, time

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
        # --- Encabezados del reporte ---
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

        # --- Columnas por día ---
        date_start = filters.get('date_start')
        date_end = filters.get('date_end')
        if isinstance(date_start, str):
            date_start = datetime.strptime(date_start, '%Y-%m-%d')
        if isinstance(date_end, str):
            date_end = datetime.strptime(date_end, '%Y-%m-%d')
        # Ajustar date_end al final del día para incluir todas las asistencias de ese día
        if date_end is not None:
            date_end = datetime.combine(date_end.date(), time(23, 59, 59))

        date_columns = [d.strftime('%d/%m') for d in pd.date_range(date_start, date_end, freq='D')]
        header.extend(date_columns)

        rows = [header]

        # --- Dominio base para empleados ---
        domain_emp = []
        if filters.get('company_id'):
            domain_emp.append(('company_id', '=', filters['company_id']))
        if filters.get('department_id'):
            domain_emp.append(('department_id', '=', filters['department_id']))

        # --- Obtener empleados (optimizado con search_read) ---
        fields_emp = [
            'id', 'employee_number', 'name', 'employment_start_date',
            'company_id', 'department_id', 'job_id', 'payment_type'
        ]
        employees_read = env['hr.employee'].search_read(domain_emp, fields_emp)

        def rel_name(val):
            return val[1] if isinstance(val, (list, tuple)) and len(val) > 1 else ''

        df_emp = pd.DataFrame.from_records(employees_read)
        if df_emp.empty:
            return rows

        df_emp['empresa'] = df_emp['company_id'].apply(rel_name)
        df_emp['departamento'] = df_emp['department_id'].apply(rel_name)
        df_emp['puesto'] = df_emp['job_id'].apply(rel_name)

        payment_map = dict(env['hr.employee']._fields['payment_type'].selection) if 'payment_type' in env['hr.employee']._fields else {}
        df_emp['tipo_pago'] = df_emp['payment_type'].map(lambda v: payment_map.get(v, v if v else 'N/A'))

        df_emp = df_emp.rename(columns={
            'employee_number': 'numero',
            'name': 'nombre',
            'employment_start_date': 'fecha_ingreso'
        })
        df_emp = df_emp[['id', 'numero', 'nombre', 'fecha_ingreso', 'empresa', 'departamento', 'puesto', 'tipo_pago']]
        df_emp['numero'] = df_emp['numero'].fillna('N/A')

        # --- Asistencias ---
        domain_att = []
        if filters.get('date_start'):
            domain_att.append(('check_in', '>=', date_start))
        if filters.get('date_end'):
            domain_att.append(('check_in', '<=', date_end))
        # filtrar por company/department en attendances si se pasó el filtro
        if filters.get('company_id'):
            domain_att.append(('employee_id.company_id', '=', filters['company_id']))
        if filters.get('department_id'):
            domain_att.append(('employee_id.department_id', '=', filters['department_id']))

        attendances = env['hr.attendance'].search_read(domain_att, ['employee_id', 'check_in'])
        df_att = pd.DataFrame.from_records(attendances)

        if not df_att.empty:
            df_att['check_in'] = pd.to_datetime(df_att['check_in'])
            df_att['employee_id'] = df_att['employee_id'].apply(lambda v: v[0] if v else None)
            df_att['retardo'] = (df_att['check_in'].dt.hour > 8) | ((df_att['check_in'].dt.hour == 8) & (df_att['check_in'].dt.minute > 10))
            df_stats = df_att.groupby('employee_id').agg(
                asistencias=('check_in', 'count'),
                retardos=('retardo', 'sum')
            ).reset_index()
        else:
            df_stats = pd.DataFrame(columns=['employee_id', 'asistencias', 'retardos'])

        # --- Ausencias (Vacaciones, Incapacidades, Permisos) ---
        leave_domain = [
            ('state', '=', 'validate'),
            ('date_from', '<=', date_end),
            ('date_to', '>=', date_start),
        ]
        # si quieres limitar leaves por empresa/departamento se puede añadir filtrando por employee_id a partir de df_emp['id']
        leaves = env['hr.leave'].search_read(leave_domain, ['employee_id', 'holiday_status_id', 'date_from', 'date_to'])
        df_leave = pd.DataFrame.from_records(leaves)

        if not df_leave.empty:
            df_leave['employee_id'] = df_leave['employee_id'].apply(lambda v: v[0] if v else None)
            df_leave['tipo'] = df_leave['holiday_status_id'].apply(lambda v: v[1] if isinstance(v, (list, tuple)) and len(v) > 1 else '')
            df_leave['desde'] = pd.to_datetime(df_leave['date_from'])
            df_leave['hasta'] = pd.to_datetime(df_leave['date_to'])
        else:
            df_leave = pd.DataFrame(columns=['employee_id', 'tipo', 'desde', 'hasta'])

        def count_days_type(df, name, date_start, date_end):
            if df.empty:
                return pd.DataFrame(columns=['employee_id', name])
            mask = df['tipo'].str.contains(name, case=False, na=False)
            df_type = df[mask].copy()
            # Calcular días de cada registro dentro del periodo del reporte
            df_type['desde_clip'] = df_type['desde'].apply(lambda d: max(d, date_start))
            df_type['hasta_clip'] = df_type['hasta'].apply(lambda d: min(d, date_end))
            df_type['dias'] = (df_type['hasta_clip'] - df_type['desde_clip']).dt.days + 1
            # Solo contar días positivos
            df_type['dias'] = df_type['dias'].clip(lower=0)
            return df_type.groupby('employee_id')['dias'].sum().reset_index(name=name)

        df_vac = count_days_type(df_leave, 'Vacaciones', date_start, date_end)
        df_inc = count_days_type(df_leave, 'Incapacidad', date_start, date_end)
        df_perm = count_days_type(df_leave, 'Permiso', date_start, date_end)

        df = df_emp.merge(df_stats, how='left', left_on='id', right_on='employee_id')
        df = df.merge(df_vac, how='left', on='employee_id')
        df = df.merge(df_inc, how='left', on='employee_id')
        df = df.merge(df_perm, how='left', on='employee_id')

        df[['asistencias', 'retardos', 'Vacaciones', 'Incapacidad', 'Permiso']] = df[
            ['asistencias', 'retardos', 'Vacaciones', 'Incapacidad', 'Permiso']
        ].fillna(0).astype(int)

        business_days = pd.date_range(date_start, date_end, freq='B')
        total_dias_habiles = len(business_days)
        df['Faltas'] = total_dias_habiles - (df['asistencias'] + df['Vacaciones'] + df['Incapacidad'] + df['Permiso'])
        df['Faltas'] = df['Faltas'].clip(lower=0)

        if not df['fecha_ingreso'].isnull().all():
            df['fecha_ingreso'] = pd.to_datetime(df['fecha_ingreso'], errors='coerce').dt.strftime('%Y-%m-%d')

        # --- Marcación por día ---
        for _, emp in df.iterrows():
            emp_id = emp['id']
            daily_marks = []
            for day in pd.date_range(date_start, date_end, freq='D'):
                att_day = df_att[
                    (df_att['employee_id'] == emp_id) & (df_att['check_in'].dt.date == day.date())
                ]
                if not att_day.empty:
                    mark = 'R' if att_day['retardo'].any() else 'A'
                else:
                    lv_day = df_leave[
                        (df_leave['employee_id'] == emp_id) &
                        (df_leave['desde'].dt.date <= day.date()) &
                        (df_leave['hasta'].dt.date >= day.date())
                    ]
                    if not lv_day.empty:
                        tipo = lv_day.iloc[0]['tipo'].lower()
                        if 'vacac' in tipo:
                            mark = 'V'
                        elif 'incap' in tipo:
                            mark = 'I'
                        elif 'perm' in tipo:
                            mark = 'P'
                        else:
                            mark = '-'
                    else:
                        mark = 'F'
                daily_marks.append(mark)

            rows.append([
                emp['numero'],
                emp['nombre'],
                emp['fecha_ingreso'] if pd.notna(emp['fecha_ingreso']) else 'N/A',
                emp['empresa'],
                emp['departamento'],
                emp['puesto'],
                emp['tipo_pago'],
                int(emp['asistencias']),
                int(emp['Vacaciones']),
                int(emp['retardos']),
                int(emp['Incapacidad']),
                int(emp['Permiso']),
                int(emp['Faltas']),
                *daily_marks
            ])

        return rows
