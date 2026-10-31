import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """Empleados que ya estaban dados de baja y seguían como aprobadores de tiempo personal o
    asistencia de otros: esos empleados pasan a tener al usuario de su jefe directo, si sigue
    activo, o quedan sin aprobador, igual que pasa ahora al dar de baja."""
    env = api.Environment(cr, SUPERUSER_ID, {'active_test': False})
    former = env['hr.employee'].search([('active', '=', False)])
    if former:
        reassigned = former._reassign_approvers_on_termination()
        _logger.info("Bajas anteriores: aprobadores reasignados en %s empleados", len(reassigned))
