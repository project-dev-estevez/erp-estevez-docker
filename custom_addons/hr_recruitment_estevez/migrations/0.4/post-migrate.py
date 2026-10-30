import logging

from odoo import SUPERUSER_ID, api

from odoo.addons.hr_recruitment_estevez.website_postings import apply_postings

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """Publica las vacantes que la 0.3 no encontró por diferencias en el nombre del puesto
    (Coordinador de Almacén General, Auxiliar de Gestión de Talento, Auxiliar de Compras).
    Las que ya están publicadas con su página no se tocan."""
    env = api.Environment(cr, SUPERUSER_ID, {})
    missing = apply_postings(env, skip_published=True)
    if missing:
        _logger.warning("Revisar en Reclutamiento → Puestos: %s", ", ".join(missing))
