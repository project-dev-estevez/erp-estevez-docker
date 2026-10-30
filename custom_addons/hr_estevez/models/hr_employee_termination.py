import logging

from odoo import SUPERUSER_ID, models

_logger = logging.getLogger(__name__)


class HrEmployee(models.Model):
    """Al dar de baja a un empleado (archivarlo), sus contratos en curso, en borrador o
    vencidos pasan a Cancelado y su usuario se desactiva. Cubre el asistente "Dar de baja" y el
    archivado directo, porque ambos terminan escribiendo active=False."""
    _inherit = 'hr.employee'

    def write(self, vals):
        leaving = self.filtered('active') if 'active' in vals and not vals['active'] else self.browse()
        res = super().write(vals)
        if leaving:
            leaving._cancel_contracts_on_termination()
            leaving._deactivate_users_on_termination()
        return res

    def _deactivate_users_on_termination(self):
        """Desactiva el usuario de los empleados dados de baja. Se respeta el usuario que tenga
        otro empleado activo (p. ej. en otra empresa), el superusuario y el usuario que hace la
        baja, porque Odoo no permite desactivarse a uno mismo."""
        users = self.user_id.filtered(lambda u: u.active and u.id != SUPERUSER_ID and u != self.env.user)
        still_employed = self.env['hr.employee'].sudo().search([
            ('user_id', 'in', users.ids),
            ('id', 'not in', self.ids),
        ]).user_id
        users = (users - still_employed).sudo()
        if users:
            users.write({'active': False})
            _logger.info("Baja de empleados %s: usuarios %s desactivados", self.ids, users.ids)
        return users

    def _cancel_contracts_on_termination(self):
        contracts = self.env['hr.contract'].sudo().search([
            ('employee_id', 'in', self.ids),
            ('state', 'in', ('draft', 'open', 'close')),
        ])
        if contracts:
            contracts.write({'state': 'cancel'})
            _logger.info("Baja de empleados %s: contratos %s cancelados", self.ids, contracts.ids)
        return contracts
