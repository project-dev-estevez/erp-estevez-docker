import base64
import io

from PIL import Image

LOGIN_PAGE_PARAM_KEYS = (
    'auth_estevez.login_page_logo',
    'auth_estevez.login_page_background_image',
)


def make_png(color='red', size=(3, 3)):
    """PNG en base64, distinto del 1x1 transparente que se usa como respaldo."""
    buffer = io.BytesIO()
    Image.new('RGB', size, color).save(buffer, format='PNG')
    return base64.b64encode(buffer.getvalue())


def save_settings(env, **values):
    """Guarda Ajustes igual que el botón "Guardar" del formulario."""
    env['res.config.settings'].create(values).execute()
