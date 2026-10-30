import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """Empleados que ya estaban dados de baja (archivados) antes de que existiera la
    cancelación automática: sus contratos en curso, en borrador o vencidos pasan a Cancelado,
    igual que pasa ahora al dar de baja."""
    env = api.Environment(cr, SUPERUSER_ID, {'active_test': False})
    former = env['hr.employee'].search([('active', '=', False)])
    if former:
        cancelled = former._cancel_contracts_on_termination()
        _logger.info("Bajas anteriores: %s contratos cancelados de %s empleados",
                     len(cancelled), len(cancelled.employee_id))
