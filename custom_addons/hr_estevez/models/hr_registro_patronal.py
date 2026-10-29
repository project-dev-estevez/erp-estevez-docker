from odoo import _, api, fields, models
from odoo.exceptions import UserError


class HrRegistroPatronal(models.Model):
    _name = 'hr.registro.patronal'
    _description = 'Registro Patronal'
    _order = 'code'
    _rec_names_search = ['code', 'name']

    code = fields.Char(string='Registro Patronal', required=True)
    name = fields.Char(string='Descripción', required=True)
    active = fields.Boolean(string='Activo', default=True)
    employee_ids = fields.One2many('hr.employee', 'registro_patronal_id', string='Empleados')
    employee_count = fields.Integer(string='Empleados', compute='_compute_employee_count')

    _sql_constraints = [
        ('code_unique', 'unique(code)', 'Ya existe un registro patronal con ese número.'),
    ]

    @api.depends('code', 'name')
    def _compute_display_name(self):
        for record in self:
            record.display_name = f"{record.code} - {record.name}" if record.name else record.code

    def _compute_employee_count(self):
        groups = self.env['hr.employee'].with_context(active_test=False)._read_group(
            [('registro_patronal_id', 'in', self.ids)], ['registro_patronal_id'], ['__count'])
        counts = {registro.id: count for registro, count in groups}
        for record in self:
            record.employee_count = counts.get(record.id, 0)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('code'):
                vals['code'] = vals['code'].strip().upper()
        return super().create(vals_list)

    def write(self, vals):
        if vals.get('code'):
            vals['code'] = vals['code'].strip().upper()
        return super().write(vals)

    @api.ondelete(at_uninstall=False)
    def _unlink_except_assigned_employees(self):
        # Incluye empleados archivados para no dejar referencias huérfanas
        employees = self.env['hr.employee'].with_context(active_test=False).search(
            [('registro_patronal_id', 'in', self.ids)])
        if employees:
            raise UserError(_(
                "No se puede eliminar el registro patronal %(registro)s porque tiene %(count)s "
                "empleado(s) asignado(s). Reasígnalos o archiva el registro en su lugar.",
                registro=', '.join(employees.registro_patronal_id.mapped('display_name')),
                count=len(employees),
            ))

    def action_view_employees(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Empleados'),
            'res_model': 'hr.employee',
            'view_mode': 'list,form',
            'domain': [('registro_patronal_id', '=', self.id)],
            'context': {'active_test': False, 'default_registro_patronal_id': self.id},
        }
