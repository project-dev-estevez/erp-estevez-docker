# -*- coding: utf-8 -*-
from datetime import timedelta

from odoo import fields
from odoo.tests.common import TransactionCase

from odoo.addons.hr_recruitment_estevez.models.hr_recruitment_executive_dashboard import _is_candidate_decline


class TestRecruitmentExecutiveDashboard(TransactionCase):
    """Indicadores del dashboard de Dirección de Reclutamiento"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        Stage = cls.env['hr.recruitment.stage']
        cls.first_contact = Stage.create({'name': 'Primer contacto KPI', 'sequence': 1001})
        cls.interview = Stage.create({'name': 'Entrevista KPI', 'sequence': 1002})
        cls.medical = Stage.create({'name': 'Examen médico KPI', 'sequence': 1003})
        cls.hired_stage = Stage.create({'name': 'Contratado KPI', 'sequence': 1004, 'hired_stage': True})
        cls.source = cls.env['utm.source'].create({'name': 'Fuente KPI'})
        cls.job = cls.env['hr.job'].create({'name': 'Puesto KPI'})
        cls.counter = 0

    def _applicant(self, stage, skipped_from=None):
        self.__class__.counter += 1
        candidate = self.env['hr.candidate'].create({
            'first_name': f'Candidato {self.counter}', 'last_name': 'KPI', 'partner_name': f'Candidato {self.counter}'})
        applicant = self.env['hr.applicant'].create({
            'candidate_id': candidate.id, 'first_name': f'Candidato {self.counter}', 'last_name': 'KPI',
            'mother_last_name': 'Prueba', 'job_id': self.job.id, 'source_id': self.source.id,
            'stage_id': (skipped_from or self.first_contact).id,
        })
        if stage != (skipped_from or self.first_contact):
            applicant.write({'stage_id': stage.id})
        return applicant

    def _funnel(self, applicants):
        dashboard = self.env['hr.recruitment.executive.dashboard']
        # Solo las etapas de esta prueba (las de datos demo tienen otros nombres)
        levels = dashboard._funnel(applicants)['levels']
        return {lvl['label']: lvl['count'] for lvl in levels}

    def test_candidate_decline_classification(self):
        self.assertTrue(_is_candidate_decline('Candidato declinó: salario bajo'))
        self.assertTrue(_is_candidate_decline('Aceptó otra oferta'))
        self.assertTrue(_is_candidate_decline('No se presentó a la entrevista'))
        # "Falta de experiencia" es un rechazo de la empresa, no del candidato
        self.assertFalse(_is_candidate_decline('Falta de experiencia'))
        self.assertFalse(_is_candidate_decline('No cumple el perfil'))

    def test_funnel_counts_reached_stages(self):
        at_first = self._applicant(self.first_contact)
        at_interview = self._applicant(self.interview)
        at_medical = self._applicant(self.medical)
        hired = self._applicant(self.hired_stage)
        counts = self._funnel(at_first | at_interview | at_medical | hired)
        # "Llegó al menos a esta etapa": cada nivel incluye a los que avanzaron más
        self.assertEqual(counts['Primer contacto KPI'], 4)
        self.assertEqual(counts['Entrevista KPI'], 3)
        self.assertEqual(counts['Examen médico KPI'], 2)
        self.assertEqual(counts['Contratados'], 1)

    def test_funnel_counts_skipped_stage(self):
        # Quien saltó de primer contacto a examen médico también "pasó" por entrevista
        jumped = self._applicant(self.medical)
        counts = self._funnel(jumped)
        self.assertEqual(counts['Entrevista KPI'], 1)
        self.assertEqual(counts['Examen médico KPI'], 1)

    def test_dashboard_runs_for_period(self):
        self._applicant(self.interview)
        today = fields.Date.today()
        data = self.env['hr.recruitment.executive.dashboard'].get_dashboard_data(
            fields.Date.to_string(today - timedelta(days=30)), fields.Date.to_string(today))
        for key in ('kpis', 'funnel', 'recruiters', 'bottlenecks', 'sources', 'rejections', 'alerts'):
            self.assertIn(key, data)
        self.assertGreaterEqual(data['kpis']['applicants'], 1)
