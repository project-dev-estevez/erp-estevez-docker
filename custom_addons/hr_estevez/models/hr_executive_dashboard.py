from collections import Counter, defaultdict
from datetime import timedelta

from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import AccessError

# Agrupación de los tipos de baja de hr.employee.history para la lectura directiva
TERMINATION_GROUPS = {
    'voluntary_resignation': 'voluntaria',
    'abandonment': 'voluntaria',
    'contract_end': 'fin_contrato',
    'dismissal_misconduct': 'involuntaria',
    'dismissal_performance': 'involuntaria',
    'dismissal_probity': 'involuntaria',
}
TERMINATION_GROUP_LABELS = {
    'voluntaria': 'Voluntaria',
    'involuntaria': 'Involuntaria',
    'fin_contrato': 'Fin de contrato',
    'sin_especificar': 'Sin especificar',
}

# Rangos de antigüedad en meses: (etiqueta, desde, hasta)
TENURE_BINS = [
    ('< 3 meses', 0, 3),
    ('3–12 meses', 3, 12),
    ('1–3 años', 12, 36),
    ('3–5 años', 36, 60),
    ('5+ años', 60, None),
]

EARLY_TURNOVER_DAYS = 90
ALLOWED_PERIODS = (3, 6, 12, 24)
MONTH_LABELS = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']


class HrExecutiveDashboard(models.AbstractModel):
    _name = 'hr.executive.dashboard'
    _description = 'Dashboard de Dirección (RH)'

    @api.model
    def get_filter_options(self):
        return {
            'companies': [{'id': c.id, 'name': c.name} for c in self.env.user.company_ids],
            'directions': self.env['hr.direction'].search_read([], ['name'], order='name'),
            'periods': list(ALLOWED_PERIODS),
        }

    @api.model
    def get_dashboard_data(self, months=12, company_id=False, direction_id=False):
        months = months if months in ALLOWED_PERIODS else 12
        today = fields.Date.context_today(self)
        window_start = today.replace(day=1) - relativedelta(months=months - 1)
        prev_start = window_start - relativedelta(months=months)

        employee_domain = []
        if company_id:
            employee_domain.append(('company_id', '=', company_id))
        if direction_id:
            employee_domain.append(('direction_id', '=', direction_id))
        employees = self.env['hr.employee'].with_context(active_test=False).search(employee_domain)
        active_employees = employees.filtered('active')

        tz_date = lambda dt: fields.Datetime.context_timestamp(self, dt).date()

        # Inicio laboral: fecha de ingreso capturada; si falta, primer contrato o fecha de alta en Odoo
        start = {}
        for employee in employees:
            start[employee.id] = (employee.employment_start_date or employee.first_contract_date
                                  or tz_date(employee.create_date))

        # Bajas: historial del asistente de baja; si no existe, departure_date del empleado archivado
        exits = []  # (employee, fecha, tipo)
        history = self.env['hr.employee.history'].search(
            [('status', '=', 'baja'), ('employee_id', 'in', employees.ids)], order='date')
        with_history = set()
        for record in history:
            exits.append((record.employee_id, tz_date(record.date), record.termination_type or False))
            with_history.add(record.employee_id.id)
        for employee in employees - active_employees:
            if employee.id not in with_history and employee.departure_date:
                exits.append((employee, employee.departure_date, False))

        # Fin laboral (para reconstruir la plantilla en el tiempo) solo de empleados archivados
        end = {}
        missing_exit_date = 0
        last_exit = {}
        for employee, exit_date, _type in exits:
            last_exit[employee.id] = max(exit_date, last_exit.get(employee.id, exit_date))
        for employee in employees - active_employees:
            if employee.id in last_exit:
                end[employee.id] = last_exit[employee.id]
            else:
                end[employee.id] = tz_date(employee.write_date)
                missing_exit_date += 1

        def headcount_at(day, ids=None):
            pool = ids if ids is not None else start.keys()
            return sum(1 for eid in pool
                       if start[eid] <= day and (eid not in end or end[eid] > day))

        def window_exits(date_from, date_to):
            # Una baja por empleado por mes
            seen, result = set(), []
            for employee, exit_date, exit_type in exits:
                key = (employee.id, exit_date.year, exit_date.month)
                if date_from <= exit_date <= date_to and key not in seen:
                    seen.add(key)
                    result.append((employee, exit_date, exit_type))
            return result

        def turnover(date_from, date_to):
            rows, total_exits, averages = [], 0, []
            cursor = date_from
            while cursor <= date_to:
                month_end = min(cursor + relativedelta(months=1, days=-1), today)
                hc_start = headcount_at(cursor - timedelta(days=1))
                hc_end = headcount_at(month_end)
                month_exits = window_exits(cursor, month_end)
                month_hires = [eid for eid, d in start.items() if cursor <= d <= month_end]
                average = (hc_start + hc_end) / 2
                averages.append(average)
                total_exits += len(month_exits)
                rows.append({
                    'label': f"{MONTH_LABELS[cursor.month - 1]} {str(cursor.year)[2:]}",
                    'date_from': fields.Date.to_string(cursor),
                    'date_to': fields.Date.to_string(month_end),
                    'headcount': hc_end,
                    'hires': len(month_hires),
                    'exits': len(month_exits),
                    'rate': round(len(month_exits) / average * 100, 1) if average else 0.0,
                    'hire_ids': month_hires,
                    'exit_ids': list({e.id for e, _d, _t in month_exits}),
                })
                cursor += relativedelta(months=1)
            average = sum(averages) / len(averages) if averages else 0
            rate = round(total_exits / average * 100, 1) if average else 0.0
            return rows, total_exits, average, rate

        monthly, total_exits, average_hc, rate = turnover(window_start, today)
        _prev_rows, prev_exits, _prev_avg, prev_rate = turnover(prev_start, window_start - timedelta(days=1))
        period_exits = window_exits(window_start, today)

        # Rotación temprana: bajas con menos de 90 días de antigüedad al salir
        early = [e for e, d, _t in period_exits if (d - start[e.id]).days < EARLY_TURNOVER_DAYS]

        tenure_days = [(today - start[e.id]).days for e in active_employees if start[e.id] <= today]
        headcount_now = len(active_employees)
        headcount_start = headcount_at(window_start - timedelta(days=1))

        return {
            'period': {'months': months, 'date_from': fields.Date.to_string(window_start),
                       'date_to': fields.Date.to_string(today)},
            'kpis': {
                'headcount': headcount_now,
                'headcount_delta': headcount_now - headcount_start,
                'turnover_rate': rate,
                'turnover_delta': round(rate - prev_rate, 1),
                'exits': total_exits,
                'prev_exits': prev_exits,
                'average_headcount': round(average_hc, 1),
                'early_turnover_rate': round(len(early) / len(period_exits) * 100, 1) if period_exits else 0.0,
                'early_exits': len(early),
                'early_exit_ids': [e.id for e in early],
                'avg_tenure_years': round(sum(tenure_days) / len(tenure_days) / 365.25, 1) if tenure_days else 0.0,
                'active_ids': active_employees.ids,
            },
            'monthly': monthly,
            'reasons': self._reasons(period_exits),
            'departments': self._departments(employees, period_exits, headcount_at, window_start, today),
            'tenure': self._tenure(active_employees, start, today),
            'alerts': self._alerts(active_employees, employee_domain, company_id, direction_id, today),
            'data_quality': {
                'missing_start_date': len(active_employees.filtered(lambda e: not e.employment_start_date)),
                'missing_exit_date': missing_exit_date,
            },
        }

    def _reasons(self, period_exits):
        labels = dict(self.env['hr.employee.history']._fields['termination_type'].selection)
        counts, ids = Counter(), defaultdict(set)
        for employee, _date, exit_type in period_exits:
            key = exit_type or 'sin_especificar'
            counts[key] += 1
            ids[key].add(employee.id)
        total = sum(counts.values())
        return [{
            'key': key,
            'label': labels.get(key, _('Sin especificar')),
            'group': TERMINATION_GROUPS.get(key, 'sin_especificar'),
            'group_label': TERMINATION_GROUP_LABELS[TERMINATION_GROUPS.get(key, 'sin_especificar')],
            'count': count,
            'pct': round(count / total * 100, 1) if total else 0.0,
            'employee_ids': sorted(ids[key]),
        } for key, count in counts.most_common()]

    def _departments(self, employees, period_exits, headcount_at, window_start, today):
        by_department = defaultdict(list)
        for employee in employees:
            by_department[employee.department_id].append(employee.id)
        exits_by_department = defaultdict(set)
        for employee, _date, _type in period_exits:
            exits_by_department[employee.department_id].add(employee.id)
        rows = []
        for department, ids in by_department.items():
            average = (headcount_at(window_start - timedelta(days=1), ids) + headcount_at(today, ids)) / 2
            exit_ids = exits_by_department.get(department, set())
            if not exit_ids or average < 1:
                continue
            rows.append({
                'id': department.id,
                'name': department.name or _('Sin área'),
                'exits': len(exit_ids),
                'average_headcount': round(average, 1),
                'rate': round(len(exit_ids) / average * 100, 1),
                'employee_ids': sorted(exit_ids),
            })
        # Primero donde más se pierde gente; la tasa desempata y da contexto
        rows.sort(key=lambda r: (r['exits'], r['rate']), reverse=True)
        return rows[:8]

    def _tenure(self, active_employees, start, today):
        rows = [{'label': label, 'count': 0, 'employee_ids': []} for label, _f, _t in TENURE_BINS]
        for employee in active_employees:
            months_in = relativedelta(today, start[employee.id])
            total_months = months_in.years * 12 + months_in.months
            for row, (_label, low, high) in zip(rows, TENURE_BINS):
                if total_months >= low and (high is None or total_months < high):
                    row['count'] += 1
                    row['employee_ids'].append(employee.id)
                    break
        return rows

    def _alerts(self, active_employees, employee_domain, company_id, direction_id, today):
        alerts = []
        employee_ids = active_employees.ids

        def add(key, severity, count, label, detail, res_model, domain):
            alerts.append({'key': key, 'severity': severity, 'count': count, 'label': label,
                           'detail': detail, 'res_model': res_model, 'domain': domain})

        contract_model = self.env['hr.contract']
        expiring_domain = [('state', '=', 'open'), ('employee_id', 'in', employee_ids),
                           ('date_end', '>=', fields.Date.to_string(today)),
                           ('date_end', '<=', fields.Date.to_string(today + timedelta(days=30)))]
        add('contracts_expiring', 'critical', contract_model.search_count(expiring_domain),
            _('contratos vencen en los próximos 30 días'), _('Decidir renovación o salida'),
            'hr.contract', expiring_domain)

        with_contract = contract_model.search([('state', '=', 'open'), ('employee_id', 'in', employee_ids)]).employee_id
        without_contract = active_employees - with_contract
        add('no_contract', 'warning', len(without_contract), _('empleados activos sin contrato vigente'),
            _('Riesgo laboral: regularizar contrato'), 'hr.employee', [('id', 'in', without_contract.ids)])

        missing_start = active_employees.filtered(lambda e: not e.employment_start_date)
        add('missing_start', 'warning', len(missing_start), _('empleados sin fecha de ingreso'),
            _('Afecta antigüedad, vacaciones y estos indicadores'), 'hr.employee', [('id', 'in', missing_start.ids)])

        month_start = fields.Datetime.to_string(fields.Datetime.to_datetime(today.replace(day=1)))
        memo_domain = [('employee_id', 'in', employee_ids), ('date', '>=', month_start)]
        add('memorandums', 'info', self.env['hr.memorandum'].search_count(memo_domain),
            _('actas administrativas este mes'), _('Indicador de clima y disciplina'), 'hr.memorandum', memo_domain)

        # Módulos opcionales: solo si están instalados y el usuario puede leerlos
        if 'hr.incapacity' in self.env:
            try:
                incapacity_domain = [('employee_id', 'in', employee_ids), ('state', '=', 'validate'),
                                     ('start_date', '<=', fields.Date.to_string(today)),
                                     ('end_date', '>=', fields.Date.to_string(today))]
                add('incapacities', 'info', self.env['hr.incapacity'].search_count(incapacity_domain),
                    _('incapacidades activas hoy'), _('Ausencias que cubrir'), 'hr.incapacity', incapacity_domain)
            except AccessError:
                pass
        if 'hr.requisition' in self.env:
            try:
                vacancy_domain = [('state', '=', 'approved'), ('is_published', '=', True)]
                if company_id:
                    vacancy_domain.append(('company_id', '=', company_id))
                if direction_id:
                    vacancy_domain.append(('direction_id', '=', direction_id))
                vacancies = self.env['hr.requisition'].search(vacancy_domain)
                open_days = [(today - tz_d).days for tz_d in
                             (fields.Datetime.context_timestamp(self, v.publish_date).date()
                              for v in vacancies if v.publish_date)]
                detail = (_('Promedio %s días abiertas', round(sum(open_days) / len(open_days)))
                          if open_days else _('Posiciones por cubrir'))
                add('vacancies', 'info', len(vacancies), _('vacantes abiertas'), detail,
                    'hr.requisition', vacancy_domain)
            except AccessError:
                pass
        return alerts
