from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

class HRCandidate(models.Model):
    _inherit = 'hr.candidate'
    _description = 'HR Candidate Extended'

    source_id = fields.Many2one(
        'utm.source',
        string="Fuente de reclutamiento",
        help="Fuente desde la cual llegó el candidato (LinkedIn, referencia, etc.)"
    )

    @api.constrains('first_name', 'last_name', 'mother_last_name')
    def _constrain_check_duplicate_full_name(self):
        for record in self:
            # Solo validar si los tres campos están completos
            if all([record.first_name, record.last_name, record.mother_last_name]):
                # Normalizar los nombres para comparación
                first = (record.first_name or '').strip().lower()
                last = (record.last_name or '').strip().lower()
                mother = (record.mother_last_name or '').strip().lower()
                
                # Buscar coincidencias exactas
                domain = [
                    ('first_name', '=ilike', first),
                    ('last_name', '=ilike', last),
                    ('mother_last_name', '=ilike', mother),
                    ('id', '!=', record.id),
                ]
                
                existing = self.search_count(domain)
                if existing:
                    full_name = f"{first.title()} {last.title()} {mother.title()}"
                    raise ValidationError(
                        f"Ya existe un candidato registrado con el nombre: {full_name}."
                    )