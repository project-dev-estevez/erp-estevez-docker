from odoo import fields, models, api

class HrEmployee(models.Model):
    _inherit = "hr.employee"
    
    project_id = fields.Many2one(
        'project.project',
        string='Proyecto',
        help='Proyecto asignado al empleado'
    )
    
    first_name = fields.Char(string="Nombre(s)")    
    last_name_1 = fields.Char(string="Apellido Paterno")
    last_name_2 = fields.Char(string="Apellido Materno")
    names = fields.Char(string="Nombre Completo")
    direction_id = fields.Many2one('hr.direction', string='Dirección')
    area_id = fields.Many2one('hr.area', string='Area')

    @api.onchange('first_name', 'last_name_1', 'last_name_2')
    def _onchange_name_fields(self):
        for rec in self:
            full_name = ' '.join(filter(None, [rec.first_name, rec.last_name_1, rec.last_name_2]))
            rec.name = full_name.strip()

    def _compute_full_name(self):
        return ' '.join(filter(None, [
            self.first_name,            
            self.last_name_1,
            self.last_name_2,
        ])).strip()

    @api.model
    def create(self, vals):
        if not vals.get('name'):
            vals['name'] = ' '.join(filter(None, [
                vals.get('first_name'),                
                vals.get('last_name_1'),
                vals.get('last_name_2'),
            ])).strip()
        return super().create(vals)

    def write(self, vals):
        res = super().write(vals)
        if any(k in vals for k in ['first_name', 'last_name_1', 'last_name_2']):
            for rec in self:
                rec.name = rec._compute_full_name()
        return res

    def action_open_documents(self):
        self.env['hr.applicant.document'].search([]).unlink()
        docs = self.env['hr.applicant.document'].create_required_documents(self.id)

        return {
            'name': _('Documentos del Aplicanteeeeee'),
            'view_mode': 'kanban',
            'res_model': 'hr.applicant.document',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {'create': False},
            'views': [(self.env.ref('hr_recruitment_estevez.view_hr_applicant_documents_kanban').id, 'kanban')],  # Asegúrate de usar la vista correcta
        }