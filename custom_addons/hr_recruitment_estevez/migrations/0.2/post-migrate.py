import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """Nuevo flujo de requisiciones (Borrador → Aprobación Dirección → Aprobación final → Aprobada).

    - Las requisiciones que se quedaron capturadas a medias (sin puesto) en «Por aprobar» pasan a
      Borrador: antes se creaban al dar «Siguiente» aunque nunca se terminaran.
    - Las demás reciben folio (con el año en que se crearon) y su fecha de envío.
    """
    env = api.Environment(cr, SUPERUSER_ID, {'tracking_disable': True, 'mail_notrack': True})
    Requisition = env['hr.requisition']

    incomplete = Requisition.search([('state', '=', 'to_approve'), ('workstation_job_id', '=', False)])
    incomplete.write({'state': 'draft'})
    _logger.info("Requisiciones incompletas regresadas a Borrador: %s", len(incomplete))

    sent = Requisition.search([('state', '!=', 'draft'), ('folio', '=', False)], order='create_date, id')
    for requisition in sent:
        requisition.write({
            'folio': env['ir.sequence'].next_by_code('hr.requisition', sequence_date=requisition.create_date),
            'submit_date': requisition.create_date,
        })
    _logger.info("Folios asignados a requisiciones existentes: %s", len(sent))
