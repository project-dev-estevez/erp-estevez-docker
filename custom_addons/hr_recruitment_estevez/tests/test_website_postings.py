# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase

from odoo.addons.hr_recruitment_estevez.website_postings import POSTINGS, apply_postings


class TestWebsitePostings(TransactionCase):
    """Publicación de las vacantes activas en la sección Empleos"""

    def test_apply_postings_publishes_jobs(self):
        Job = self.env['hr.job'].with_context(active_test=False)
        Job.search([('name', 'in', [p['job'] for p in POSTINGS])]).write({'name': 'Puesto anterior'})
        chofer = Job.create({'name': 'Chofer', 'active': False})

        missing = apply_postings(self.env)

        self.assertTrue(chofer.active)
        self.assertTrue(chofer.is_published)
        self.assertEqual(chofer.no_of_recruitment, 1)
        self.assertIn('Chofer Ejecutivo de Dirección General', chofer.website_description)
        self.assertNotIn('$15,000', chofer.website_description)  # sin sueldo publicado
        self.assertIn(f'/jobs/apply/{self.env["ir.http"]._slug(chofer)}', chofer.website_description)
        # Los puestos que no existen se reportan y no truenan la migración
        self.assertIn('Analista de Compras', missing)
        self.assertNotIn('Chofer', missing)
