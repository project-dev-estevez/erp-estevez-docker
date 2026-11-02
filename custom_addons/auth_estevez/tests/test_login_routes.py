import base64

from odoo.tests.common import HttpCase, tagged

from .common import make_png, save_settings

ACCESS_SCREENS = {
    '/web/login': 'Iniciar Sesión',
    '/web/reset_password': 'Restablecer contraseña',
    '/web/signup': 'Crear cuenta',
}


@tagged('auth_estevez', 'post_install', '-at_install')
class TestLoginRoutes(HttpCase):
    """Pantallas de acceso e imágenes (docs/spec.md, secciones 4.2 y 4.3)."""

    def setUp(self):
        super().setUp()
        params = self.env['ir.config_parameter'].sudo()
        params.set_param('auth_signup.reset_password', 'True')
        params.set_param('auth_signup.invitation_scope', 'b2c')

    def _get_html(self, url):
        response = self.url_open(url)
        self.assertEqual(response.status_code, 200, url)
        return response.text

    def test_root_and_design_classes(self):
        """AUTH-06: cada pantalla trae la clase raíz y la del diseño vigente."""
        save_settings(self.env, login_page_design='boxed_right')
        for url in ACCESS_SCREENS:
            with self.subTest(url=url):
                html = self._get_html(url)
                self.assertIn('o_auth_estevez', html)
                self.assertIn('o_login--boxed_right', html)

    def test_titles_per_screen(self):
        """AUTH-07: cada pantalla muestra su título."""
        for url, title in ACCESS_SCREENS.items():
            with self.subTest(url=url):
                self.assertIn(title, self._get_html(url))

    def test_url_cannot_override_design(self):
        """AUTH-08: un parámetro en la URL no cambia el diseño configurado."""
        save_settings(self.env, login_page_design='fullscreen_left')
        html = self._get_html('/web/login?login_page_design=boxed_center')
        self.assertIn('o_login--fullscreen_left', html)
        self.assertNotIn('o_login--boxed_center', html)

    def test_no_global_state_mutation(self):
        """AUTH-09: servir el login no agrega claves a SIGN_UP_REQUEST_PARAMS."""
        from odoo.addons.web.controllers.home import SIGN_UP_REQUEST_PARAMS

        self._get_html('/web/login')
        leaked = sorted(key for key in SIGN_UP_REQUEST_PARAMS if key.startswith('login_page_'))
        self.assertFalse(leaked, f"Claves agregadas al estado global: {leaked}")

    def test_motto_toggle(self):
        """AUTH-10: el lema solo se renderiza cuando está activo."""
        save_settings(
            self.env,
            login_page_design='fullscreen_left',
            login_page_show_motto=True,
            login_page_motto_text='Juntos llegamos más lejos',
            login_page_motto_author='Estevez.Jor',
        )
        html = self._get_html('/web/login')
        self.assertIn('Juntos llegamos más lejos', html)
        self.assertIn('Estevez.Jor', html)

        save_settings(self.env, login_page_design='fullscreen_left', login_page_show_motto=False)
        self.assertNotIn('login-quote', self._get_html('/web/login'))

    def test_image_fallback(self):
        """AUTH-11: sin imagen configurada se sirve un PNG de respaldo."""
        save_settings(self.env, login_page_logo=False, login_page_background_image=False)
        for url in ('/login_logo.png', '/login_page_background_image.png'):
            with self.subTest(url=url):
                response = self.url_open(url)
                self.assertEqual(response.status_code, 200)
                self.assertTrue(response.headers['Content-Type'].startswith('image/png'))

    def test_configured_logo_served(self):
        """AUTH-12: con logo configurado se sirven sus bytes y su mimetype."""
        logo = make_png('red')
        save_settings(self.env, login_page_logo=logo)

        response = self.url_open('/login_logo.png')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.headers['Content-Type'].startswith('image/png'))
        self.assertEqual(response.content, base64.b64decode(logo))
