import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)

# Titulares del organigrama: (modelo, campo del titular, campo del puesto del titular,
# campo del empleado que lo liga a ese nivel). Dirección > Área (hr.department) > Departamento (hr.area).
ORG_HEADS = (
    ('hr.direction', 'director_id', 'director_job_id', 'direction_id'),
    ('hr.department', 'manager_id', 'manager_job_id', 'department_id'),
    ('hr.area', 'coordinator_id', 'coordinator_job_id', 'area_id'),
)
ORG_HEAD_TRIGGER_FIELDS = {'active', 'job_id', 'direction_id', 'department_id', 'area_id'}


class HrDirection(models.Model):
    _inherit = 'hr.direction'

    director_job_id = fields.Many2one(
        'hr.job', string='Puesto del director',
        help='Quien ocupe este puesto en la dirección queda como director cuando la dirección no tenga uno vigente.')


class HrDepartment(models.Model):
    _inherit = 'hr.department'

    manager_job_id = fields.Many2one(
        'hr.job', string='Puesto del gerente',
        help='Quien ocupe este puesto en el área queda como gerente cuando el área no tenga uno vigente.')


class HrArea(models.Model):
    _inherit = 'hr.area'

    coordinator_job_id = fields.Many2one(
        'hr.job', string='Puesto del coordinador',
        help='Quien ocupe este puesto en el departamento queda como coordinador cuando el departamento no tenga uno vigente.')


class HrEmployee(models.Model):
    """Mantiene al día al director, gerente y coordinador de cada nivel del organigrama.

    - Al dar de baja a un empleado, deja de ser titular de cualquier dirección, área o departamento.
    - Al asignar a un empleado activo el puesto del titular dentro de ese nivel, ocupa la titularidad
      si está vacante o si el titular anterior ya no tiene ese puesto ahí. Si el titular sigue vigente
      no se le reemplaza (p. ej. dos personas con el mismo puesto).
    """
    _inherit = 'hr.employee'

    @api.model_create_multi
    def create(self, vals_list):
        employees = super().create(vals_list)
        employees._sync_org_heads()
        return employees

    def write(self, vals):
        res = super().write(vals)
        if ORG_HEAD_TRIGGER_FIELDS & set(vals):
            self._sync_org_heads()
        return res

    def _sync_org_heads(self):
        # Cambiar al gerente de un área reasigna el jefe directo de su gente (Odoo estándar);
        # esas escrituras no cambian datos que se envíen a System, así que no se sincronizan.
        env = self.env(su=True, context=dict(self.env.context, skip_codeigniter_sync=True))
        leaving = self.filtered(lambda e: not e.active)
        for model, head_field, job_field, link_field in ORG_HEADS:
            Unit = env[model]
            if leaving:
                units = Unit.search([(head_field, 'in', leaving.ids)])
                if units:
                    units.write({head_field: False})
                    _logger.info("Baja de empleados %s: %s %s quedan sin %s",
                                 leaving.ids, model, units.ids, head_field)
            for employee in self.filtered('active'):
                unit = Unit.browse(employee[link_field].id)
                if not unit or not employee.job_id or unit[job_field] != employee.job_id:
                    continue
                head = unit[head_field]
                if head == employee:
                    continue
                if head and head.active and head.job_id == unit[job_field] and head[link_field] == unit:
                    continue
                unit.write({head_field: employee.id})
                _logger.info("%s %s: %s pasa de %s a %s", model, unit.id, head_field, head.id, employee.id)
