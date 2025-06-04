from odoo import models, fields, api
from odoo.exceptions import UserError

class HRCandidate(models.Model):
    _inherit = 'hr.candidate'

    source_id = fields.Many2one(
        'utm.source',
        string="Fuente de reclutamiento",
        help="Fuente desde la cual llegó el candidato (LinkedIn, referencia, etc.)."
    )

    @api.onchange('partner_name')
    def _onchange_check_duplicate_name(self):
        if self.partner_name:
            # Buscar candidatos distintos a este, con el mismo nombre
            existing = self.env['hr.candidate'].search([
                ('partner_name', '=', self.partner_name),
                ('id', '!=', self.id),
            ])
            if existing:
                return {
                    'warning': {
                        'title': "Candidato ya existe",
                        'message': f"Ya existe un candidato registrado con el nombre '{self.partner_name}'."
                    }
                }
