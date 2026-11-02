from odoo.tests.common import TransactionCase, tagged

from .common import LOGIN_PAGE_PARAM_KEYS, make_png, save_settings

DEFAULT_DESIGN = 'fullscreen_left'
DEFAULT_MOTTO_COLOR = '#000000'


@tagged('auth_estevez')
class TestLoginPageValues(TransactionCase):
    """Valores de la página de acceso (docs/spec.md, sección 4.1)."""

    def setUp(self):
        super().setUp()
        self.company = self.env.ref('base.main_company')

    def test_default_design(self):
        """AUTH-01: sin configurar, el diseño es fullscreen_left."""
        new_company = self.env['res.company'].create({'name': 'Compañía sin configurar'})
        self.assertEqual(new_company._get_login_page_values()['login_page_design'], DEFAULT_DESIGN)

        # Registros previos a la migración: columna en NULL
        self.env.cr.execute(
            "UPDATE res_company SET login_page_design = NULL WHERE id = %s", [self.company.id])
        self.company.invalidate_recordset(['login_page_design'])
        self.assertEqual(self.company._get_login_page_values()['login_page_design'], DEFAULT_DESIGN)

    def test_invalid_design_falls_back(self):
        """AUTH-02: un diseño fuera de la lista cae en fullscreen_left."""
        self.env.cr.execute(
            "UPDATE res_company SET login_page_design = 'no_existe' WHERE id = %s", [self.company.id])
        self.company.invalidate_recordset(['login_page_design'])
        self.assertEqual(self.company._get_login_page_values()['login_page_design'], DEFAULT_DESIGN)

    def test_motto_color_sanitized(self):
        """AUTH-03: solo se aceptan colores hex; lo demás cae en #000000."""
        cases = {
            False: DEFAULT_MOTTO_COLOR,
            '': DEFAULT_MOTTO_COLOR,
            'red': DEFAULT_MOTTO_COLOR,
            '#12': DEFAULT_MOTTO_COLOR,
            '#000;background:url(https://evil.example)': DEFAULT_MOTTO_COLOR,
            '#abc': '#abc',
            '#A1B2C3': '#A1B2C3',
        }
        for stored, expected in cases.items():
            with self.subTest(stored=stored):
                self.company.login_page_motto_text_color = stored
                values = self.company._get_login_page_values()
                self.assertEqual(values['login_page_motto_text_color'], expected)

    def test_settings_round_trip(self):
        """AUTH-04: lo que se guarda en Ajustes es lo que se vuelve a leer."""
        expected = {
            'login_page_design': 'boxed_right',
            'login_page_custom_background': True,
            'login_page_show_motto': True,
            'login_page_motto_text': 'Juntos llegamos más lejos',
            'login_page_motto_author': 'Estevez.Jor',
            'login_page_motto_text_color': '#1f2937',
        }
        save_settings(self.env, **expected)

        settings = self.env['res.config.settings'].create({})
        for field_name, value in expected.items():
            with self.subTest(field=field_name):
                self.assertEqual(settings[field_name], value)

    def test_images_stored_on_company(self):
        """AUTH-05: logo y fondo quedan en la compañía, no en ir.config_parameter."""
        logo, background = make_png('red'), make_png('blue')
        save_settings(self.env, login_page_logo=logo, login_page_background_image=background)

        self.assertIn('login_page_logo', self.company._fields)
        self.assertIn('login_page_background_image', self.company._fields)
        self.assertEqual(self.company.login_page_logo, logo)
        self.assertEqual(self.company.login_page_background_image, background)
        self.assertFalse(
            self.env['ir.config_parameter'].sudo().search_count(
                [('key', 'in', LOGIN_PAGE_PARAM_KEYS)]),
            "Las imágenes no deben guardarse en ir.config_parameter",
        )
