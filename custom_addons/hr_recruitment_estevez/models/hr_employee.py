from odoo import fields, models, api, _

class HrEmployee(models.Model):
    _inherit = "hr.employee"
    
    project_id = fields.Many2one(
        'project.project',
        string='Proyecto',
        help='Proyecto asignado al empleado'
    )
    
    first_name = fields.Char(string="Nombre(s)", required=True)    
    last_name = fields.Char(string="Apellido Paterno", required=True)
    mother_last_name = fields.Char(string="Apellido Materno", required=True)    
    direction_id = fields.Many2one('hr.direction', string='Dirección')
    area_id = fields.Many2one('hr.area', string='Area')

    @api.onchange('first_name', 'last_name', 'mother_last_name')
    def _onchange_name_fields(self):
        for rec in self:
            full_name = ' '.join(filter(None, [rec.first_name, rec.last_name, rec.mother_last_name]))
            rec.name = full_name.strip()

    def _compute_full_name(self):
        # Filtrar campos None y strings vacíos, excluyendo "Sin especificar"
        name_parts = []
        for field_value in [self.first_name, self.last_name, self.mother_last_name]:
            if field_value and field_value != "Sin especificar":
                name_parts.append(field_value)
        return ' '.join(name_parts).strip()

    @api.model
    def create(self, vals):
        # Solo usar valores reales, no los placeholder
        name_parts = []
        for field in ['first_name', 'last_name', 'mother_last_name']:
            if vals.get(field) and vals[field] != "Sin especificar":
                name_parts.append(vals[field])
        
        if name_parts and not vals.get('name'):
            vals['name'] = ' '.join(name_parts).strip()
        
        return super().create(vals)

    def write(self, vals):
        res = super().write(vals)
        if any(k in vals for k in ['first_name', 'last_name', 'mother_last_name']):
            for rec in self:
                rec.name = rec._compute_full_name()
        return res

    def action_open_documents(self):
        self.env['hr.applicant.document'].search([]).unlink()
        docs = self.env['hr.applicant.document'].create_required_documents(self.id)

        return {
            'name': _('Documentos del Aplicante'),
            'view_mode': 'kanban',
            'res_model': 'hr.applicant.document',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {'create': False},
            'views': [(self.env.ref('hr_recruitment_estevez.view_hr_applicant_documents_kanban').id, 'kanban')], 
        }