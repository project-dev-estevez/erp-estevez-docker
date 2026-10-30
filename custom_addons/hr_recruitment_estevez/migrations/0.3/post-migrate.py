import logging

from odoo import SUPERUSER_ID, api

from odoo.addons.hr_recruitment_estevez.website_postings import apply_postings

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """Vacantes activas al 30/10/2026: se activan y publican en Empleos con su página nueva."""
    env = api.Environment(cr, SUPERUSER_ID, {})
    missing = apply_postings(env)
    if missing:
        _logger.warning("Revisar en Reclutamiento → Puestos: %s", ", ".join(missing))
