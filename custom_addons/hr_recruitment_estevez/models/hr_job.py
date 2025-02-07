from odoo import models, fields, api
from odoo.exceptions import UserError

class HrJob(models.Model):
    _inherit = 'hr.job'

    requisition_id = fields.Many2one('hr.requisition', string="Requisición Asociada", domain="[('state', '=', 'approved')]")
    is_requisition_required = fields.Boolean(string="¿Requisición Obligatoria?", default=True)

    @api.model
    def create(self, vals):
        if self.is_requisition_required and not vals.get('requisition_id'):
            raise UserError("No puedes crear una vacante sin una requisición aprobada.")
        return super(HrJob, self).create(vals)