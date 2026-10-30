# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase

from odoo.addons.hr_recruitment_estevez.website_postings import POSTINGS, apply_postings


class TestWebsitePostings(TransactionCase):
    """Publicación de las vacantes activas en la sección Empleos"""

    def test_apply_postings_publishes_jobs(self):
        Job = self.env['hr.job'].with_context(active_test=False)
        names = [name for posting in POSTINGS for name in posting['job']]
        Job.search([('name', 'in', names)]).write({'name': 'Puesto anterior'})
        chofer = Job.create({'name': 'Chofer', 'active': False})
        # Sin acentos ni mayúsculas también coincide, y se usa el nombre alterno del puesto
        compras = Job.create({'name': 'auxiliar de compras'})
        talento = Job.create({'name': 'Auxiliar de Gestion de Talento'})

        missing = apply_postings(self.env)

        self.assertTrue(chofer.active)
        self.assertTrue(chofer.is_published)
        self.assertEqual(chofer.no_of_recruitment, 1)
        self.assertIn('Chofer Ejecutivo de Dirección General', chofer.website_description)
        self.assertNotIn('$15,000', chofer.website_description)  # sin sueldo publicado
        self.assertIn(f'/jobs/apply/{self.env["ir.http"]._slug(chofer)}', chofer.website_description)
        self.assertTrue(compras.is_published)
        self.assertIn('Auxiliar de Compras', compras.website_description)
        self.assertTrue(talento.is_published)
        # Los puestos que no existen se reportan y no truenan la migración
        self.assertIn('Coordinador de Almacén General', missing)
        self.assertNotIn('Chofer', missing)

    def test_skip_published_keeps_edited_pages(self):
        chofer = self.env['hr.job'].with_context(active_test=False).search([('name', '=', 'Chofer')], limit=1) \
            or self.env['hr.job'].create({'name': 'Chofer'})
        apply_postings(self.env)
        chofer.website_description = '<section class="o_estevez_job">Editado en el sitio</section>'
        apply_postings(self.env, skip_published=True)
        self.assertIn('Editado en el sitio', chofer.website_description)
