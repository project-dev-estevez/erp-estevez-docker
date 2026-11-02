import importlib.util

from odoo.tests.common import TransactionCase, tagged
from odoo.tools import file_path

from .common import make_png


def load_migration(version, script):
    path = file_path(f'auth_estevez/migrations/{version}/{script}')
    spec = importlib.util.spec_from_file_location(f'auth_estevez_{script[:-3]}', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@tagged('auth_estevez')
class TestMigrationToCompany(TransactionCase):
    """Migración de ir.config_parameter a res.company (docs/spec.md, AUTH-18 y AUTH-19)."""

    def setUp(self):
        super().setUp()
        self.company = self.env.ref('base.main_company')
        self.params = self.env['ir.config_parameter'].sudo()

    def _run_migration(self):
        load_migration('18.0.2.0.0', 'post-migrate.py').migrate(self.env.cr, '18.0.1.0.0')
        self.env.invalidate_all()

    def test_legacy_params_move_to_company(self):
        """AUTH-18: los valores pasan a la compañía y los parámetros desaparecen."""
        logo = make_png('red').decode()
        legacy = {
            'auth_estevez.login_page_design': 'boxed_left',
            'auth_estevez.login_page_custom_background': 'True',
            'auth_estevez.login_page_logo': logo,
            'auth_estevez.login_page_show_motto': 'True',
            'auth_estevez.login_page_motto_text': 'Juntos llegamos más lejos',
            'auth_estevez.login_page_motto_author': 'Estevez.Jor',
            'auth_estevez.login_page_motto_text_color': '#1f2937',
        }
        for key, value in legacy.items():
            self.params.set_param(key, value)

        self._run_migration()

        self.assertRecordValues(self.company, [{
            'login_page_design': 'boxed_left',
            'login_page_custom_background': True,
            'login_page_show_motto': True,
            'login_page_motto_text': 'Juntos llegamos más lejos',
            'login_page_motto_author': 'Estevez.Jor',
            'login_page_motto_text_color': '#1f2937',
        }])
        self.assertEqual(self.company.login_page_logo.decode(), logo)
        self.assertFalse(self.params.search_count([('key', '=like', 'auth_estevez.%')]))

    def test_invalid_legacy_design_is_ignored(self):
        """AUTH-18: un diseño que ya no existe no se copia."""
        self.company.login_page_design = 'boxed_right'
        self.params.set_param('auth_estevez.login_page_design', 'no_existe')

        self._run_migration()

        self.assertEqual(self.company.login_page_design, 'boxed_right')

    def test_login_page_company(self):
        """AUTH-19: sin sesión se usa la compañía principal; con sesión, la del usuario."""
        Company = self.env['res.company']
        self.assertEqual(Company._get_login_page_company(), self.company)

        other_company = Company.create({'name': 'Otra compañía'})
        user = self.env['res.users'].create({
            'name': 'Usuario de otra compañía',
            'login': 'otra_compania@example.com',
            'company_id': other_company.id,
            'company_ids': [other_company.id],
        })
        self.assertEqual(Company._get_login_page_company(user.id), other_company)
