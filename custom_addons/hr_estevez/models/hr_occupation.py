from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class HrOccupation(models.Model):
    _inherit = 'hr.occupation'
    _order = 'code'
    _rec_names_search = ['code', 'name']

    employee_count = fields.Integer(string='Empleados', compute='_compute_employee_count')

    def _compute_employee_count(self):
        groups = self.env['hr.employee'].with_context(active_test=False)._read_group(
            [('occupation_id', 'in', self.ids)], ['occupation_id'], ['__count'])
        counts = {occupation.id: count for occupation, count in groups}
        for record in self:
            record.employee_count = counts.get(record.id, 0)

    @api.constrains('code')
    def _check_code_unique(self):
        for record in self:
            if self.search_count([('code', '=', record.code), ('id', '!=', record.id)]):
                raise ValidationError(_("Ya existe una ocupación con la clave %s.", record.code))

    @api.ondelete(at_uninstall=False)
    def _unlink_except_assigned_employees(self):
        # Incluye empleados archivados para no dejar referencias huérfanas
        employees = self.env['hr.employee'].with_context(active_test=False).search(
            [('occupation_id', 'in', self.ids)])
        if employees:
            raise UserError(_(
                "No se puede eliminar la ocupación %(ocupacion)s porque tiene %(count)s "
                "empleado(s) asignado(s). Reasígnalos antes de eliminarla.",
                ocupacion=', '.join(employees.occupation_id.mapped('display_name')),
                count=len(employees),
            ))

    def action_view_employees(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Empleados'),
            'res_model': 'hr.employee',
            'view_mode': 'list,form',
            'domain': [('occupation_id', '=', self.id)],
            'context': {'active_test': False, 'default_occupation_id': self.id},
        }
