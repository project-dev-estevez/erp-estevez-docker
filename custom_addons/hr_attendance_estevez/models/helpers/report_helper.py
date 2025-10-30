from odoo import models
import pytz  # type: ignore
import pandas as pd # type: ignore
import random
from datetime import datetime, time
import holidays
import logging
_logger = logging.getLogger(__name__)

class ReportHelper(models.AbstractModel):

    _name = 'hr_attendance_estevez.report_helper'
    _description = 'Helpers para reportes de asistencias y nómina'

    @staticmethod
    def _extract_m2o_name(value):
        """Extrae el nombre de un campo many2one (lista/tupla [id, nombre]) o retorna '' si no aplica."""
        return value[1] if isinstance(value, (list, tuple)) and len(value) > 1 else ''

    @staticmethod
    def _get_payment_type_display(value, payment_map):
        """Traduce el valor técnico de payment_type a su etiqueta legible."""
        if value:
            return payment_map.get(value, value)
        return 'N/A'

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
        """Genera las filas del reporte de nómina con asistencia y ausencias."""
        # 1️⃣ Preparar rango de fechas y encabezados
        header, date_start, date_end = self._prepare_header(filters)
        rows = [header]

        # 2️⃣ Obtener empleados base
        df_emp = self._get_employees_df(env, filters)
        if df_emp.empty:
            return rows

        # 3️⃣ Obtener estadísticas de asistencias -> Total de asistencias y Total de retardos
        df_stats, df_att = self._get_attendance_stats(env, filters, date_start, date_end)

        # 4️⃣ Obtener y procesar ausencias
        df_leave = self._get_leaves_df(env, date_start, date_end)
        _logger.info("Contenido de df_leave:\n%s", df_leave)
        df_vac = self._count_days_type(df_leave, 'vacacion', date_start, date_end)
        df_inc = self._count_days_type(df_leave, 'incapacidad', date_start, date_end)
        df_perm = self._count_days_type(df_leave, 'permiso', date_start, date_end)

        # 5️⃣ Combinar todo en un solo DataFrame
        df_combined = self._combine_all_data(df_emp, df_stats, df_vac, df_inc, df_perm, date_start, date_end)

        # 6️⃣ Generar las filas finales
        rows.extend(self._generate_rows(df_combined, df_att, df_leave, date_start, date_end))

        return rows

    # -------------------------------------------------------------------------
    # 1️⃣ Encabezado y rango de fechas
    # -------------------------------------------------------------------------
    def _prepare_header(self, filters):
        header = [
            'Numero Empleado', 'Nombre Completo', 'Fecha de Ingreso', 'Empresa',
            'Departamento', 'Puesto', 'Tipo Pago', 'Asistencias', 'Vacaciones',
            'Retardos', 'Incapacidades', 'Permisos', 'Faltas'
        ]

        date_start = self._parse_date(filters.get('date_start'))
        date_end = self._parse_date(filters.get('date_end'), end_of_day=True)

        date_columns = [
            d.strftime('%d/%m')
            for d in pd.date_range(date_start, date_end, freq='D')
        ]
        header.extend(date_columns)
        return header, date_start, date_end

    def _parse_date(self, date_str, end_of_day=False):
        if not date_str:
            return None
        if isinstance(date_str, str):
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        else:
            date_obj = date_str
        if end_of_day and date_obj:
            return datetime.combine(date_obj.date(), time(23, 59, 59))
        return date_obj

    # -------------------------------------------------------------------------
    # 2️⃣ Empleados base
    # -------------------------------------------------------------------------
    def _get_employees_df(self, env, filters):
        domain = []
        if filters.get('company_id'):
            domain.append(('company_id', '=', filters['company_id']))
        if filters.get('department_id'):
            domain.append(('department_id', '=', filters['department_id']))

        fields = [
            'id', 'employee_number', 'name', 'employment_start_date',
            'company_id', 'department_id', 'job_id', 'payment_type'
        ]
        employees = env['hr.employee'].search_read(domain, fields)
        df = pd.DataFrame.from_records(employees)
        if df.empty:
            return df

        # Extraer nombres de campos many2one
        df['empresa'] = df['company_id'].apply(self._extract_m2o_name)
        df['departamento'] = df['department_id'].apply(self._extract_m2o_name)
        df['puesto'] = df['job_id'].apply(self._extract_m2o_name)

        # Traducir tipo de pago
        payment_map = dict(env['hr.employee']._fields['payment_type'].selection)
        df['tipo_pago'] = df['payment_type'].map(lambda v: self._get_payment_type_display(v, payment_map))

        # Renombrar columnas y limpiar datos
        df = df.rename(columns={
            'employee_number': 'numero',
            'name': 'nombre',
            'employment_start_date': 'fecha_ingreso'
        })
        df['numero'] = df['numero'].fillna('N/A')

        return df[['id', 'numero', 'nombre', 'fecha_ingreso', 'empresa', 'departamento', 'puesto', 'tipo_pago']]

    # -------------------------------------------------------------------------
    # 3️⃣ Asistencias
    # -------------------------------------------------------------------------
    def _get_attendance_stats(self, env, filters, date_start, date_end):
        domain = []
        if filters.get('date_start'):
            domain.append(('check_in', '>=', date_start))
        if filters.get('date_end'):
            domain.append(('check_in', '<=', date_end))
        if filters.get('company_id'):
            domain.append(('employee_id.company_id', '=', filters['company_id']))
        if filters.get('department_id'):
            domain.append(('employee_id.department_id', '=', filters['department_id']))

        attendances = env['hr.attendance'].search_read(domain, ['employee_id', 'check_in'])
        df_att = pd.DataFrame.from_records(attendances)
        # Asegura que las columnas existen aunque el DataFrame esté vacío y que 'check_in' sea datetime
        if df_att.empty:
            df_att = pd.DataFrame({'employee_id': pd.Series(dtype='object'),
                                   'check_in': pd.to_datetime(pd.Series([], dtype='datetime64[ns]')),
                                   'retardo': pd.Series(dtype='bool')})
            df_stats = pd.DataFrame(columns=['employee_id', 'asistencias', 'retardos'])
            return df_stats, df_att

        df_att['check_in'] = pd.to_datetime(df_att['check_in'])
        df_att['employee_id'] = df_att['employee_id'].apply(lambda v: v[0] if v else None)
        df_att['retardo'] = (df_att['check_in'].dt.hour > 8) | ((df_att['check_in'].dt.hour == 8) & (df_att['check_in'].dt.minute > 10))

        df_stats = df_att.groupby('employee_id').agg(
            asistencias=('check_in', 'count'),
            retardos=('retardo', 'sum')
        ).reset_index()

        return df_stats, df_att

    # -------------------------------------------------------------------------
    # 4️⃣ Ausencias
    # -------------------------------------------------------------------------
    def _get_leaves_df(self, env, date_start, date_end):
        leave_domain = [
            ('state', '=', 'validate'),
            ('date_from', '<=', date_end),
            ('date_to', '>=', date_start),
        ]
        leaves = env['hr.leave'].search_read(leave_domain, ['employee_id', 'holiday_status_id', 'date_from', 'date_to'])
        df = pd.DataFrame.from_records(leaves)
        if df.empty:
            return pd.DataFrame(columns=['employee_id', 'tipo', 'desde', 'hasta'])

        df['employee_id'] = df['employee_id'].apply(lambda v: v[0] if v else None)
        df['tipo'] = df['holiday_status_id'].apply(lambda v: v[1] if isinstance(v, (list, tuple)) else '')
        df['desde'] = pd.to_datetime(df['date_from']).dt.date
        df['hasta'] = pd.to_datetime(df['date_to']).dt.date
        return df[['employee_id', 'tipo', 'desde', 'hasta']]

    def _count_days_type(self, df, name, date_start, date_end):
        if df.empty:
            return pd.DataFrame(columns=['employee_id', name])

        # Comparar en minúsculas para evitar problemas de mayúsculas/minúsculas y tildes
        mask = df['tipo'].str.lower().str.contains(name.lower(), na=False)
        df_type = df[mask].copy()
        df_type['desde_clip'] = df_type['desde'].apply(lambda d: max(d, date_start.date()))
        df_type['hasta_clip'] = df_type['hasta'].apply(lambda d: min(d, date_end.date()))

        years = set(range(date_start.year, date_end.year + 1))
        mx_holidays = holidays.Mexico(years=years)

        def count_valid_days(row):
            if pd.isnull(row['desde_clip']) or pd.isnull(row['hasta_clip']) or row['desde_clip'] > row['hasta_clip']:
                return 0
            days = pd.date_range(row['desde_clip'], row['hasta_clip'], freq='D')
            return sum((day.weekday() != 6) and (day.date() not in mx_holidays) for day in days)

        df_type['dias'] = df_type.apply(count_valid_days, axis=1)
        return df_type.groupby('employee_id')['dias'].sum().reset_index(name=name)

    # -------------------------------------------------------------------------
    # 5️⃣ Combinación y faltas
    # -------------------------------------------------------------------------
    def _combine_all_data(self, df_emp, df_stats, df_vac, df_inc, df_perm, date_start, date_end):
        df = df_emp.merge(df_stats, how='left', left_on='id', right_on='employee_id')
        for extra_df in [df_vac, df_inc, df_perm]:
            df = df.merge(extra_df, how='left', on='employee_id')

        df = df.fillna({'asistencias': 0, 'retardos': 0, 'Vacaciones': 0, 'Incapacidad': 0, 'Permiso': 0})
        df[['asistencias', 'retardos', 'Vacaciones', 'Incapacidad', 'Permiso']] = df[
            ['asistencias', 'retardos', 'Vacaciones', 'Incapacidad', 'Permiso']
        ].astype(int)

        total_dias_habiles = len(pd.date_range(date_start, date_end, freq='B'))
        df['Faltas'] = total_dias_habiles - (df['asistencias'] + df['Vacaciones'] + df['Incapacidad'] + df['Permiso'])
        df['Faltas'] = df['Faltas'].clip(lower=0)

        df['fecha_ingreso'] = pd.to_datetime(df['fecha_ingreso'], errors='coerce').dt.strftime('%Y-%m-%d')

        # 🧩 SANITIZACIÓN FINAL PARA EVITAR NaN / INF
        df = df.replace([float('inf'), float('-inf')], 0)
        df = df.fillna({'numero': 'N/A', 'nombre': 'N/A', 'empresa': '', 'departamento': '', 'puesto': '', 'tipo_pago': ''})
        df = df.fillna(0)

        return df

    # -------------------------------------------------------------------------
    # 6️⃣ Generación de filas finales
    # -------------------------------------------------------------------------
    def _generate_rows(self, df, df_att, df_leave, date_start, date_end):
        rows = []
        date_range = pd.date_range(date_start, date_end, freq='D')
        for _, emp in df.iterrows():
            marks = [self._get_daily_mark(emp['id'], day, df_att, df_leave) for day in date_range]
            rows.append([
                emp['numero'], emp['nombre'], emp['fecha_ingreso'] or 'N/A',
                emp['empresa'], emp['departamento'], emp['puesto'], emp['tipo_pago'],
                emp['asistencias'], emp['Vacaciones'], emp['retardos'],
                emp['Incapacidad'], emp['Permiso'], emp['Faltas'], *marks
            ])
        return rows

    def _get_daily_mark(self, emp_id, day, df_att, df_leave):
        att_day = df_att[
            (df_att['employee_id'] == emp_id) &
            (df_att['check_in'].dt.date == day.date())
        ]
        if not att_day.empty:
            return 'R' if att_day['retardo'].any() else 'A'

        lv_day = df_leave[
            (df_leave['employee_id'] == emp_id) &
            (df_leave['desde'] <= day.date()) &
            (df_leave['hasta'] >= day.date())
        ]
        if lv_day.empty:
            return 'F'

        tipo = lv_day.iloc[0]['tipo'].lower()
        if 'vacac' in tipo:
            return 'V'
        if 'incap' in tipo:
            return 'I'
        if 'perm' in tipo:
            return 'P'
        return '-'