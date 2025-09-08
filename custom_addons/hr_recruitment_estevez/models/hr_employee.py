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
        return ' '.join(filter(None, [
            self.first_name,            
            self.last_name,
            self.mother_last_name,
        ])).strip()

    @api.model
    def create(self, vals):
        # Asegurar que todos los campos requeridos tengan valor
        required_fields = ['first_name', 'last_name', 'mother_last_name']
        for field in required_fields:
            if field not in vals or not vals[field]:
                vals[field] = "Sin especificar"  # Valor por defecto
        
        # Generar el nombre completo
        if not vals.get('name'):
            vals['name'] = ' '.join(filter(None, [
                vals.get('first_name'),            
                vals.get('last_name'),
                vals.get('mother_last_name'),
            ])).strip()
        
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