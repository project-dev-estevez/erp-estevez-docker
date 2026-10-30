# -*- coding: utf-8 -*-
from datetime import datetime, time, timedelta

from odoo import fields
from odoo.tests.common import TransactionCase


class TestExecutiveDashboard(TransactionCase):
    """Indicadores del dashboard de Dirección (hr.executive.dashboard)"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.today = fields.Date.today()
        cls.direction = cls.env['hr.direction'].create({'name': 'Dirección de prueba KPI'})
        cls.counter = 0

        cls.actives = cls.env['hr.employee']
        for _i in range(10):
            cls.actives |= cls._employee(days_ago=730)

        # Dos renuncias de gente con más de un año y un abandono antes de 90 días
        cls.leavers = cls._employee(days_ago=400) | cls._employee(days_ago=400)
        cls.early_leaver = cls._employee(days_ago=60)
        cls._exit(cls.leavers[0], days_ago=30, termination_type='voluntary_resignation')
        cls._exit(cls.leavers[1], days_ago=45, termination_type='voluntary_resignation')
        cls._exit(cls.early_leaver, days_ago=10, termination_type='abandonment')

    @classmethod
    def _employee(cls, days_ago):
        cls.counter += 1
        return cls.env['hr.employee'].create({
            # create() arma el nombre con names + apellidos
            'names': f'Empleado {cls.counter}',
            'last_name': 'Prueba',
            'mother_last_name': 'KPI',
            'direction_id': cls.direction.id,
            'employment_start_date': cls.today - timedelta(days=days_ago),
            'employee_number': f'KPI{cls.counter:03d}',
            'barcode': f'KPI{cls.counter:03d}',
        })

    @classmethod
    def _exit(cls, employee, days_ago, termination_type):
        cls.env['hr.employee.history'].create({
            'employee_id': employee.id,
            'status': 'baja',
            'termination_type': termination_type,
            'date': datetime.combine(cls.today - timedelta(days=days_ago), time(12)),
        })
        employee.with_context(skip_codeigniter_sync=True).write({'active': False})

    def _data(self, months=12):
        return self.env['hr.executive.dashboard'].get_dashboard_data(months, False, self.direction.id)

    def test_headcount_and_turnover(self):
        kpis = self._data()['kpis']
        self.assertEqual(kpis['headcount'], 10)
        self.assertEqual(kpis['exits'], 3)
        # Rotación = bajas del periodo ÷ plantilla promedio del periodo
        self.assertAlmostEqual(kpis['turnover_rate'], round(3 / kpis['average_headcount'] * 100, 1), delta=0.2)

    def test_early_turnover(self):
        kpis = self._data()['kpis']
        self.assertEqual(kpis['early_exits'], 1)
        self.assertEqual(kpis['early_exit_ids'], self.early_leaver.ids)
        self.assertAlmostEqual(kpis['early_turnover_rate'], 33.3, places=1)

    def test_reasons_grouped(self):
        reasons = {r['key']: r for r in self._data()['reasons']}
        self.assertEqual(reasons['voluntary_resignation']['count'], 2)
        self.assertEqual(reasons['abandonment']['count'], 1)
        self.assertTrue(all(r['group'] == 'voluntaria' for r in reasons.values()))

    def test_tenure_bins_and_filter(self):
        data = self._data()
        tenure = {t['label']: t['count'] for t in data['tenure']}
        self.assertEqual(tenure['1–3 años'], 10)
        self.assertEqual(sum(tenure.values()), 10)
        # Ninguno tiene contrato vigente: todos aparecen en la alerta
        alerts = {a['key']: a['count'] for a in data['alerts']}
        self.assertEqual(alerts['no_contract'], 10)

    def test_short_period_excludes_older_exits(self):
        # En 3 meses entran las tres bajas (10, 30 y 45 días); el periodo anterior no tiene ninguna
        kpis = self._data(months=3)['kpis']
        self.assertEqual(kpis['exits'], 3)
        self.assertEqual(kpis['prev_exits'], 0)
