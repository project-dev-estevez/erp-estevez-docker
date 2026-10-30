import logging

from odoo import SUPERUSER_ID, api

from odoo.addons.hr_estevez.models.hr_org_heads import ORG_HEADS

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """Pone al día el organigrama con las reglas nuevas de bajas:

    1. Cada dirección, área y departamento toma como "puesto del titular" el puesto de su
       director, gerente o coordinador actual (aunque ya sea baja), para que quien ocupe ese
       puesto después quede como titular.
    2. Los titulares que ya estaban dados de baja se quitan.
    3. Los usuarios de empleados que ya estaban dados de baja se desactivan.
    """
    env = api.Environment(cr, SUPERUSER_ID, {'active_test': False})
    for model, head_field, job_field, _link_field in ORG_HEADS:
        units = env[model].search([(head_field, '!=', False), (job_field, '=', False)])
        for unit in units.filtered(lambda u: u[head_field].job_id):
            unit[job_field] = unit[head_field].job_id
        _logger.info("%s: puesto del titular tomado del titular actual en %s registros", model, len(units))

    former = env['hr.employee'].search([('active', '=', False)])
    if former:
        former._sync_org_heads()
        users = former._deactivate_users_on_termination()
        _logger.info("Bajas anteriores: %s usuarios desactivados", len(users))
