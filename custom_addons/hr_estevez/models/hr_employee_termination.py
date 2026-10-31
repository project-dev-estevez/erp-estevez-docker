import logging

from odoo import SUPERUSER_ID, models

_logger = logging.getLogger(__name__)

# Aprobadores de tiempo personal (hr_holidays) y asistencia (hr_attendance) del empleado
APPROVER_FIELDS = ('leave_manager_id', 'attendance_manager_id')


class HrEmployee(models.Model):
    """Al dar de baja a un empleado (archivarlo), sus contratos en curso, en borrador o
    vencidos pasan a Cancelado, deja de ser aprobador de otros empleados y su usuario se
    desactiva. Cubre el asistente "Dar de baja" y el archivado directo, porque ambos terminan
    escribiendo active=False."""
    _inherit = 'hr.employee'

    def write(self, vals):
        leaving = self.filtered('active') if 'active' in vals and not vals['active'] else self.browse()
        res = super().write(vals)
        if leaving:
            leaving._cancel_contracts_on_termination()
            leaving._reassign_approvers_on_termination()
            leaving._deactivate_users_on_termination()
        return res

    def _departing_users(self):
        """Usuarios de estos empleados que no tienen otro empleado activo (p. ej. en otra empresa)."""
        still_employed = self.env['hr.employee'].sudo().with_context(active_test=True).search([
            ('user_id', 'in', self.user_id.ids),
            ('id', 'not in', self.ids),
        ]).user_id
        return self.user_id - still_employed

    def _deactivate_users_on_termination(self):
        """Desactiva el usuario de los empleados dados de baja. Se respeta el superusuario y el
        usuario que hace la baja, porque Odoo no permite desactivarse a uno mismo."""
        users = self._departing_users().filtered(
            lambda u: u.active and u.id != SUPERUSER_ID and u != self.env.user).sudo()
        if users:
            users.write({'active': False})
            _logger.info("Baja de empleados %s: usuarios %s desactivados", self.ids, users.ids)
        return users

    def _reassign_approvers_on_termination(self):
        """Quien tenía como aprobador de tiempo personal o asistencia a un empleado dado de baja
        pasa a tener al usuario de su jefe directo, si sigue activo, o queda sin aprobador."""
        departing = self._departing_users()
        # Los aprobadores no se envían a System, así que estas escrituras no se sincronizan
        Employee = self.env['hr.employee'].sudo().with_context(skip_codeigniter_sync=True)
        reassigned = Employee
        for field in APPROVER_FIELDS:
            if not departing or field not in Employee._fields:
                continue
            for employee in Employee.search([(field, 'in', departing.ids)]):
                boss = employee.parent_id.user_id
                employee[field] = boss if boss.active and boss not in departing else False
                reassigned |= employee
        if reassigned:
            _logger.info("Baja de usuarios %s: aprobadores reasignados en empleados %s",
                         departing.ids, reassigned.ids)
        return reassigned

    def _cancel_contracts_on_termination(self):
        contracts = self.env['hr.contract'].sudo().search([
            ('employee_id', 'in', self.ids),
            ('state', 'in', ('draft', 'open', 'close')),
        ])
        if contracts:
            contracts.write({'state': 'cancel'})
            _logger.info("Baja de empleados %s: contratos %s cancelados", self.ids, contracts.ids)
        return contracts
