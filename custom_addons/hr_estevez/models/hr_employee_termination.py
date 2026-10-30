import logging

from odoo import models

_logger = logging.getLogger(__name__)


class HrEmployee(models.Model):
    """Al dar de baja a un empleado (archivarlo), sus contratos en curso o en borrador
    pasan a Cancelado. Cubre el asistente "Dar de baja" y el archivado directo, porque
    ambos terminan escribiendo active=False."""
    _inherit = 'hr.employee'

    def write(self, vals):
        leaving = self.filtered('active') if 'active' in vals and not vals['active'] else self.browse()
        res = super().write(vals)
        if leaving:
            leaving._cancel_contracts_on_termination()
        return res

    def _cancel_contracts_on_termination(self):
        contracts = self.env['hr.contract'].sudo().search([
            ('employee_id', 'in', self.ids),
            ('state', 'in', ('draft', 'open')),
        ])
        if contracts:
            contracts.write({'state': 'cancel'})
            _logger.info("Baja de empleados %s: contratos %s cancelados", self.ids, contracts.ids)
        return contracts
