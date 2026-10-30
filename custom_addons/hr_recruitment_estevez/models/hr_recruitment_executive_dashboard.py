import re
import unicodedata
from collections import Counter, defaultdict
from datetime import datetime, time, timedelta
from statistics import median

import pytz

from odoo import _, api, fields, models

STALLED_DAYS = 7
AGING_VACANCY_DAYS = 30
RETENTION_DAYS = 90

# Motivos que indican que el candidato declinó (no que la empresa lo rechazó).
# Se compara contra el motivo normalizado (minúsculas, sin acentos ni signos).
CANDIDATE_DECLINE_PATTERNS = [
    'declino', 'declina', 'no se presento', 'no se presenta', 'no asistio', 'no asiste',
    'ausente', 'falta a', 'falto', 'inasistencia', 'solo se presenta a induccion', 'solo induccion',
    'no respondio', 'no responde', 'no contesta', 'no contesto', 'sin respuesta', 'no hay respuesta',
    'abandono', 'abandona', 'se retira', 'se retiro', 'desiste', 'desistio',
    'cambio de opinion', 'cambio opinion', 'ya no le interesa', 'perdio interes', 'perdio el interes',
    'sin interes', 'acepto otra oferta', 'acepta otra oferta', 'otra oferta', 'mejor oferta',
    'oferta mejor', 'consiguio otro trabajo', 'otro trabajo', 'otra empresa', 'no esta interesado',
    'no le interesa', 'no disponible', 'no puede', 'imposibilitado', 'problemas personales',
    'situacion personal', 'no cumple horario', 'horario no le conviene', 'salario insuficiente',
    'salario bajo', 'sueldo bajo', 'poco salario', 'distancia', 'muy lejos', 'ubicacion',
    'transporte', 'no acepta condiciones', 'condiciones no favorables', 'expectativas diferentes',
    'no es lo que busca', 'cambio de planes',
]


def _normalize(text):
    text = unicodedata.normalize('NFD', (text or '').lower())
    text = ''.join(ch for ch in text if unicodedata.category(ch) != 'Mn')
    return ' '.join(re.sub(r'[^\w\s]', ' ', text).split())


def _is_candidate_decline(label):
    normalized = _normalize(label)
    return any(pattern in normalized for pattern in CANDIDATE_DECLINE_PATTERNS)


def _days(start, end):
    return (end - start).total_seconds() / 86400


class HrRecruitmentExecutiveDashboard(models.AbstractModel):
    _name = 'hr.recruitment.executive.dashboard'
    _description = 'Dashboard de Dirección (Reclutamiento)'

    # ---------- utilidades ----------
    def _utc_bounds(self, date_from, date_to):
        """Rango de fechas locales del usuario -> datetimes UTC sin zona (como los guarda Odoo)."""
        tz = pytz.timezone(self.env.user.tz or 'UTC')
        start = tz.localize(datetime.combine(fields.Date.to_date(date_from), time.min))
        end = tz.localize(datetime.combine(fields.Date.to_date(date_to), time.max))
        return (start.astimezone(pytz.UTC).replace(tzinfo=None),
                end.astimezone(pytz.UTC).replace(tzinfo=None))

    def _scope_domain(self, recruiter_id, direction_id):
        domain = []
        if recruiter_id:
            domain.append(('user_id', '=', recruiter_id))
        if direction_id:
            domain.append(('job_id.department_id.direction_id', '=', direction_id))
        return domain

    def _applicants(self, domain):
        return self.env['hr.applicant'].with_context(active_test=False).search(domain)

    def _first_contact_sequence(self):
        stage = self.env['hr.recruitment.stage'].search([('name', 'ilike', 'primer contacto')], limit=1)
        return stage.sequence if stage else None

    @api.model
    def get_filter_options(self):
        recruiters = self.env['hr.applicant'].with_context(active_test=False).read_group(
            [('user_id', '!=', False)], ['user_id'], ['user_id'])
        return {
            'recruiters': sorted(({'id': r['user_id'][0], 'name': r['user_id'][1]} for r in recruiters),
                                 key=lambda r: r['name']),
            'directions': self.env['hr.direction'].search_read([], ['name'], order='name'),
        }

    # ---------- datos principales ----------
    @api.model
    def get_dashboard_data(self, date_from, date_to, recruiter_id=False, direction_id=False):
        start, end = self._utc_bounds(date_from, date_to)
        now = fields.Datetime.now()
        scope = self._scope_domain(recruiter_id, direction_id)

        created = self._applicants(scope + [('create_date', '>=', start), ('create_date', '<=', end)])
        # Igual que las tarjetas: una postulación cuenta desde que llega a "Primer contacto"
        first_contact = self._first_contact_sequence()
        if first_contact is not None:
            created = created.filtered(lambda a: a.stage_id.sequence >= first_contact)
        hired = self._applicants(scope + [('application_status', '=', 'hired'),
                                          ('date_closed', '>=', start), ('date_closed', '<=', end)])

        hire_days = [_days(a.create_date, a.date_closed) for a in hired if a.date_closed]

        requisitions = self._requisition_scope(direction_id)
        closed_reqs = requisitions.filtered(
            lambda r: r.publish_date and r.close_date and start <= r.close_date <= end)
        fill_days = [_days(r.publish_date, r.close_date) for r in closed_reqs]

        return {
            'kpis': {
                'time_to_hire': round(median(hire_days), 1) if hire_days else None,
                'time_to_hire_count': len(hire_days),
                'time_to_fill': round(median(fill_days), 1) if fill_days else None,
                'time_to_fill_count': len(fill_days),
                'applicants': len(created),
                'hired': len(hired),
                'hired_ids': hired.ids,
                'conversion': round(len(hired) / len(created) * 100, 1) if created else 0.0,
                **self._retention(scope, now),
            },
            'vacancies': self._vacancy_options(created, requisitions),
            'funnel': self._funnel(created),
            'recruiters': self._recruiters(created, hired, now),
            'bottlenecks': self._bottlenecks(scope, start, end),
            'sources': self._sources(created, hired),
            'rejections': self._rejections(created),
            'alerts': self._alerts(scope, requisitions, now),
        }

    @api.model
    def get_funnel(self, date_from, date_to, recruiter_id=False, direction_id=False, job_id=False):
        start, end = self._utc_bounds(date_from, date_to)
        domain = self._scope_domain(recruiter_id, direction_id) + [
            ('create_date', '>=', start), ('create_date', '<=', end)]
        if job_id:
            domain.append(('job_id', '=', job_id))
        result = self._funnel(self._applicants(domain))
        if job_id:
            result['vacancy'] = self._vacancy_detail(job_id, end)
        return result

    # ---------- secciones ----------
    def _requisition_scope(self, direction_id):
        domain = []
        if direction_id:
            domain.append(('workstation_job_id.department_id.direction_id', '=', direction_id))
        return self.env['hr.requisition'].search(domain)

    def _retention(self, scope, now):
        """De quienes se contrataron hace 3 a 12 meses, cuántos siguen tras 90 días."""
        cohort = self._applicants(scope + [
            ('application_status', '=', 'hired'),
            ('date_closed', '>=', now - timedelta(days=365)),
            ('date_closed', '<=', now - timedelta(days=RETENTION_DAYS)),
        ])
        retained = left = unlinked = 0
        history = self.env['hr.employee.history']
        for applicant in cohort:
            employee = applicant.employee_id or applicant.candidate_id.employee_id
            if not employee:
                unlinked += 1
                continue
            employee = employee.with_context(active_test=False)
            limit = applicant.date_closed + timedelta(days=RETENTION_DAYS)
            early_exit = history.search_count([('employee_id', '=', employee.id), ('status', '=', 'baja'),
                                               ('date', '<=', limit)])
            if early_exit or (not employee.active and not history.search_count(
                    [('employee_id', '=', employee.id), ('status', '=', 'baja')])):
                left += 1
            else:
                retained += 1
        measured = retained + left
        return {
            'retention_rate': round(retained / measured * 100, 1) if measured else None,
            'retention_measured': measured,
            'retention_left': left,
            'retention_unlinked': unlinked,
        }

    def _vacancy_options(self, created, requisitions):
        counts = Counter(applicant.job_id.id for applicant in created if applicant.job_id)
        open_jobs = requisitions.filtered(lambda r: r.state == 'approved' and r.is_published).workstation_job_id
        jobs = self.env['hr.job'].browse(set(counts) | set(open_jobs.ids))
        return sorted(({'id': j.id, 'name': j.name, 'applicants': counts.get(j.id, 0)} for j in jobs),
                      key=lambda j: (-j['applicants'], j['name']))

    def _vacancy_detail(self, job_id, end):
        reqs = self.env['hr.requisition'].search([('workstation_job_id', '=', job_id), ('state', '=', 'approved')])
        open_reqs = reqs.filtered('is_published')
        opened = min((r.publish_date for r in open_reqs if r.publish_date), default=False)
        return {
            'positions': sum(open_reqs.mapped('number_of_vacancies')),
            'is_open': bool(open_reqs),
            'days_open': round(_days(opened, fields.Datetime.now())) if opened else None,
        }

    def _funnel(self, applicants):
        """Embudo de "llegó al menos a esta etapa", con el historial de etapas."""
        first_contact = self._first_contact_sequence()
        stages = self.env['hr.recruitment.stage'].search([('hired_stage', '=', False)], order='sequence, id')
        if first_contact is not None:
            stages = stages.filtered(lambda s: s.sequence >= first_contact)

        # Etapa más avanzada a la que llegó cada candidato (historial + etapa actual)
        reached = {}
        history = self.env['hr.applicant.stage.history'].search_read(
            [('applicant_id', 'in', applicants.ids)], ['applicant_id', 'stage_id'])
        stage_sequence = {s.id: s.sequence for s in self.env['hr.recruitment.stage'].search([])}
        for row in history:
            seq = stage_sequence.get(row['stage_id'][0], -1)
            reached[row['applicant_id'][0]] = max(seq, reached.get(row['applicant_id'][0], -1))
        for applicant in applicants:
            reached[applicant.id] = max(applicant.stage_id.sequence, reached.get(applicant.id, -1))

        levels = []
        for stage in stages:
            ids = [a for a, seq in reached.items() if seq >= stage.sequence]
            levels.append({'key': f'stage_{stage.id}', 'label': stage.name, 'count': len(ids), 'applicant_ids': ids})
        hired_ids = applicants.filtered(lambda a: a.application_status == 'hired').ids
        levels.append({'key': 'hired', 'label': _('Contratados'), 'count': len(hired_ids),
                       'applicant_ids': hired_ids, 'is_hired': True})
        # Etapas por las que no pasó nadie se omiten (salvo la de contratados)
        levels = [lvl for lvl in levels if lvl['count'] or lvl.get('is_hired')]

        top = levels[0]['count'] if levels else 0
        for index, level in enumerate(levels):
            previous = levels[index - 1]['count'] if index else level['count']
            level['step_rate'] = round(level['count'] / previous * 100, 1) if previous else 0.0
            level['overall_rate'] = round(level['count'] / top * 100, 1) if top else 0.0
            level['drop'] = previous - level['count'] if index else 0
        return {'levels': levels, 'total': top}

    def _recruiters(self, created, hired, now):
        stalled_limit = now - timedelta(days=STALLED_DAYS)
        ongoing = self._applicants([('application_status', '=', 'ongoing'), ('active', '=', True),
                                    ('user_id', 'in', (created | hired).user_id.ids)])
        rows = defaultdict(lambda: {'applicants': 0, 'hired': 0, 'hire_days': [], 'jobs': set(),
                                    'stalled_ids': [], 'applicant_ids': []})
        for applicant in created:
            row = rows[applicant.user_id]
            row['applicants'] += 1
            row['applicant_ids'].append(applicant.id)
        for applicant in hired:
            row = rows[applicant.user_id]
            row['hired'] += 1
            if applicant.date_closed:
                row['hire_days'].append(_days(applicant.create_date, applicant.date_closed))
        for applicant in ongoing:
            row = rows[applicant.user_id]
            row['jobs'].add(applicant.job_id.id)
            if applicant.date_last_stage_update and applicant.date_last_stage_update < stalled_limit:
                row['stalled_ids'].append(applicant.id)
        result = []
        for user, row in rows.items():
            result.append({
                'id': user.id,
                'name': user.name or _('Sin reclutador'),
                'open_jobs': len(row['jobs'] - {False}),
                'applicants': row['applicants'],
                'hired': row['hired'],
                'conversion': round(row['hired'] / row['applicants'] * 100, 1) if row['applicants'] else 0.0,
                'time_to_hire': round(median(row['hire_days']), 1) if row['hire_days'] else None,
                'stalled': len(row['stalled_ids']),
                'stalled_ids': row['stalled_ids'],
                'applicant_ids': row['applicant_ids'],
            })
        result.sort(key=lambda r: (r['hired'], r['applicants']), reverse=True)
        return result

    def _bottlenecks(self, scope, start, end):
        """Días promedio que un candidato pasa en cada etapa (etapas cerradas en el periodo)."""
        applicants = self._applicants(scope)
        rows = self.env['hr.applicant.stage.history'].search_read(
            [('applicant_id', 'in', applicants.ids), ('leave_date', '>=', start), ('leave_date', '<=', end),
             ('stage_id.hired_stage', '=', False)],
            ['stage_id', 'enter_date', 'leave_date'])
        durations = defaultdict(list)
        names = {}
        for row in rows:
            durations[row['stage_id'][0]].append(_days(row['enter_date'], row['leave_date']))
            names[row['stage_id'][0]] = row['stage_id'][1]
        result = [{'id': sid, 'name': names[sid], 'avg_days': round(sum(v) / len(v), 1), 'count': len(v)}
                  for sid, v in durations.items()]
        result.sort(key=lambda r: r['avg_days'], reverse=True)
        return result[:8]

    def _sources(self, created, hired):
        rows = defaultdict(lambda: {'applicants': 0, 'hired': 0, 'applicant_ids': []})
        for applicant in created:
            rows[applicant.source_id]['applicants'] += 1
            rows[applicant.source_id]['applicant_ids'].append(applicant.id)
        for applicant in hired:
            rows[applicant.source_id]['hired'] += 1
        result = [{
            'id': source.id,
            'name': source.name or _('Sin fuente'),
            'applicants': row['applicants'],
            'hired': row['hired'],
            'effectiveness': round(row['hired'] / row['applicants'] * 100, 1) if row['applicants'] else 0.0,
            'applicant_ids': row['applicant_ids'],
        } for source, row in rows.items() if row['applicants']]
        result.sort(key=lambda r: r['applicants'], reverse=True)
        return result[:8]

    def _rejections(self, created):
        first_contact = self._first_contact_sequence()
        refused = created.filtered(lambda a: a.application_status == 'refused' and (
            first_contact is None or a.stage_id.sequence >= first_contact))
        rows = defaultdict(list)
        for applicant in refused:
            rows[applicant.refuse_reason_id].append(applicant.id)
        total = len(refused)
        result = []
        for reason, ids in rows.items():
            label = reason.name or _('Sin motivo')
            group = 'candidato' if reason and _is_candidate_decline(label) else 'empresa'
            result.append({'id': reason.id, 'label': label, 'group': group, 'count': len(ids),
                           'pct': round(len(ids) / total * 100, 1) if total else 0.0, 'applicant_ids': ids})
        result.sort(key=lambda r: r['count'], reverse=True)
        declines = sum(r['count'] for r in result if r['group'] == 'candidato')
        return {'reasons': result[:8], 'total': total,
                'candidate_share': round(declines / total * 100) if total else 0}

    def _alerts(self, scope, requisitions, now):
        alerts = []

        def add(key, severity, count, label, detail, res_model, domain):
            alerts.append({'key': key, 'severity': severity, 'count': count, 'label': label,
                           'detail': detail, 'res_model': res_model, 'domain': domain})

        aging = requisitions.filtered(lambda r: r.state == 'approved' and r.is_published and r.publish_date
                                      and r.publish_date < now - timedelta(days=AGING_VACANCY_DAYS))
        add('aging_vacancies', 'critical', len(aging), _('vacantes abiertas hace más de %s días', AGING_VACANCY_DAYS),
            _('Revisar perfil, sueldo o fuentes'), 'hr.requisition', [('id', 'in', aging.ids)])

        stalled_domain = scope + [('application_status', '=', 'ongoing'),
                                  ('date_last_stage_update', '<', now - timedelta(days=STALLED_DAYS))]
        add('stalled', 'warning', self.env['hr.applicant'].search_count(stalled_domain),
            _('candidatos sin avanzar en más de %s días', STALLED_DAYS),
            _('Riesgo de perderlos con otra oferta'), 'hr.applicant', stalled_domain)

        pending = requisitions.filtered(lambda r: r.state in ('to_approve', 'first_approval'))
        waiting = [_days(r.create_date, now) for r in pending]
        add('pending_requisitions', 'warning', len(pending), _('requisiciones esperando aprobación'),
            _('Promedio %s días esperando', round(sum(waiting) / len(waiting))) if waiting
            else _('Al día'), 'hr.requisition', [('id', 'in', pending.ids)])

        open_reqs = requisitions.filtered(lambda r: r.state == 'approved' and r.is_published)
        recent = set(self._applicants([('create_date', '>=', now - timedelta(days=14))]).job_id.ids)
        dry = open_reqs.filtered(lambda r: r.workstation_job_id.id not in recent)
        add('no_applicants', 'info', len(dry), _('vacantes sin postulantes en 14 días'),
            _('Reforzar publicación o fuentes'), 'hr.requisition', [('id', 'in', dry.ids)])
        return alerts
