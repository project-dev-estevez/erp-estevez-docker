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
    def _onchange_recruitment_name_fields(self):
        for rec in self:
            rec.names = rec.first_name
            rec.name = rec._compose_recruitment_full_name(
                first_name=rec.first_name,
                last_name=rec.last_name,
                mother_last_name=rec.mother_last_name,
            )

    def _compose_recruitment_full_name(self, first_name=None, last_name=None, mother_last_name=None):
        name_parts = []
        for field_value in [first_name, last_name, mother_last_name]:
            if field_value and field_value != "Sin especificar":
                name_parts.append(field_value)
        return ' '.join(name_parts).strip()

    @api.model
    def create(self, vals):
        if vals.get('first_name') and not vals.get('names'):
            vals['names'] = vals['first_name']
        elif vals.get('names') and not vals.get('first_name'):
            vals['first_name'] = vals['names']

        return super().create(vals)

    def write(self, vals):
        if 'first_name' in vals and 'names' not in vals:
            vals['names'] = vals['first_name']
        elif 'names' in vals and 'first_name' not in vals:
            vals['first_name'] = vals['names']

        return super().write(vals)

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