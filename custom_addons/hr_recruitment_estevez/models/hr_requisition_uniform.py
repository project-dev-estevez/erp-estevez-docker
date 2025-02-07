from odoo import models, fields

class HrRequisitionUniform(models.Model):
    _name = 'hr.requisition.uniform'
    _description = 'Uniforme de Requisición'

    name = fields.Char(string='Nombre', required=True)