import logging

from odoo import api, models, fields

_logger = logging.getLogger(__name__)

# Nombres del organigrama de la empresa: Dirección > Área (hr.department) > Departamento (hr.area) > Puesto.
# Odoo trae sus propias traducciones ("Departamentos"), que ganan sobre el texto del código,
# así que estos nombres se fijan en todos los idiomas instalados en cada actualización del módulo.
ORG_STRUCTURE_LABELS = {
    'ir.ui.menu': {
        'hr.menu_hr_department_kanban': 'Áreas',
        'hr_estevez.menu_hr_area': 'Departamentos',
    },
    'ir.actions.act_window': {
        'hr.hr_department_kanban_action': 'Áreas',
        'hr.hr_department_tree_action': 'Áreas',
        'hr_estevez.action_hr_area': 'Departamentos',
    },
}
ORG_STRUCTURE_FIELD_LABELS = {
    ('hr.employee', 'department_id'): 'Área',
    ('hr.employee', 'area_id'): 'Departamento',
    ('hr.area', 'department_id'): 'Área',
    ('hr.department', 'area_ids'): 'Departamentos',
    ('hr.direction', 'department_ids'): 'Áreas',
    ('hr.direction', 'total_departments'): 'Total Áreas',
    ('hr.job', 'department_id'): 'Área',
    ('hr.job', 'area_id'): 'Departamento',
    ('hr.requisition', 'department_id'): 'Área',
    ('hr.requisition', 'workstation_department_id'): 'Área del Puesto',
    ('hr.requisition', 'workstation_area_id'): 'Departamento del Puesto',
}
ORG_STRUCTURE_MODEL_LABELS = {
    'hr.department': 'Área',
    'hr.area': 'Departamento',
}


class HrDepartment(models.Model):
    _inherit = 'hr.department'

    # En el organigrama de la empresa hr.department es el "Área" y hr.area el "Departamento"
    area_ids = fields.One2many('hr.area', 'department_id', string='Departamentos')
    direction_id = fields.Many2one('hr.direction', string='Dirección')

    parent_id = fields.Many2one('hr.department', string='Parent Department', index=True, check_company=True, store=True)
    child_ids = fields.One2many('hr.department', 'parent_id', string='Child Departments', store=False)

    @api.model_create_multi
    def create(self, vals_list):
        departments = super(HrDepartment, self).create(vals_list)
        for vals, department in zip(vals_list, departments):
            if vals.get('manager_id'):
             manager = self.env['hr.employee'].browse(vals['manager_id'])
             manager.write({'department_id': department.id})
        return departments

    def write(self, vals):
        res = super(HrDepartment, self).write(vals)
        if 'manager_id' in vals:
         for department in self:
            manager = self.env['hr.employee'].browse(vals['manager_id'])
            manager.write({'department_id': department.id})
        return res

    @api.model
    def _apply_org_structure_labels(self):
        """Fija los nombres de Áreas y Departamentos en menús, títulos, campos y modelos.

        Se llama desde data/org_structure_labels.xml en cada actualización del módulo.
        Solo cambia textos de pantalla, nunca registros de empleados, áreas o departamentos.
        """
        langs = [code for code, _name in self.env['res.lang'].get_installed()]

        def apply(record, field_name, label):
            if record:
                record.sudo().update_field_translations(field_name, {lang: label for lang in langs})

        for _model, labels in ORG_STRUCTURE_LABELS.items():
            for xmlid, label in labels.items():
                apply(self.env.ref(xmlid, raise_if_not_found=False), 'name', label)
        for (model, field_name), label in ORG_STRUCTURE_FIELD_LABELS.items():
            # Los campos de módulos no instalados (p. ej. requisiciones) simplemente no existen
            apply(self.env['ir.model.fields'].sudo().search(
                [('model', '=', model), ('name', '=', field_name)], limit=1), 'field_description', label)
        for model, label in ORG_STRUCTURE_MODEL_LABELS.items():
            apply(self.env['ir.model'].sudo().search([('model', '=', model)], limit=1), 'name', label)
        _logger.info("hr_estevez: nombres de Áreas y Departamentos aplicados en %s", ', '.join(langs))
